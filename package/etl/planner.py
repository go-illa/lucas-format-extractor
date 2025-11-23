import pandas as pd
import json
import logging
from groq import Groq
import config
from typing import Dict, List, Any
import os

# Set up logging
logger = logging.getLogger(__name__)

def _load_prompt_template(filename: str) -> str:
    """Loads a prompt template from the prompts directory."""
    path = os.path.join(config.PROMPT_TEMPLATE_DIR, filename)
    with open(path, 'r') as f:
        return f.read()

def select_action_with_llm(table_df: pd.DataFrame, target_schema: List[Dict]) -> Dict[str, Any]:
    """
    Analyzes the table structure and selects a transformation action using an LLM.
    """
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables.")

    client = Groq(api_key=config.GROQ_API_KEY)
    
    # Prepare the data for the prompt
    sample_data = table_df.head(20).to_string()
    target_schema_str = json.dumps(target_schema, indent=2)

    prompt_template = _load_prompt_template('action_selection_prompt.txt')
    prompt = prompt_template.replace('{{target_schema}}', target_schema_str).replace('{{client_data_sample}}', sample_data)

    try:
        logger.info("AI is analyzing table structure to select a transformation action...")
        response = client.chat.completions.create(
            model=config.GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        action_details = json.loads(response.choices[0].message.content)
        logger.info(f"AI successfully selected the '{action_details.get('action')}' action.")
        return action_details
    except Exception as e:
        logger.error(f"An error occurred with the Groq API call for action selection: {e}")
        return None