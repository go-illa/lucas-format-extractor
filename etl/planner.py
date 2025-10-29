import pandas as pd
import json
import logging
from groq import Groq
import config
from typing import Dict, List,Union
import os

# Set up logging
logger = logging.getLogger(__name__)

def _load_prompt_template(filename: str) -> str:
    """Loads a prompt template from the prompts directory."""
    path = os.path.join(config.PROMPT_TEMPLATE_DIR, filename)
    with open(path, 'r') as f:
        return f.read()

def generate_transformation_plan(table_df: pd.DataFrame, target_schema: List[Dict]) -> Union[Dict, None]:
    """
    Analyzes the table structure and generates a JSON transformation plan using an LLM.
    This is Stage 2: The "Analyst".
    """
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    
    client = Groq(api_key=config.GROQ_API_KEY)
    client_columns = table_df.columns.tolist()
    sample_data = json.loads(table_df.head(3).astype(str).to_json(orient='records'))
    target_schema_dict = {field['name']: field['description'] for field in target_schema if field['name']}

    prompt_template = _load_prompt_template('mapping_plan_prompt.txt')
    prompt = prompt_template.format(
        target_schema=json.dumps(target_schema_dict, indent=2),
        client_columns=client_columns,
        sample_data=json.dumps(sample_data, indent=2)
    )

    try:
        logger.info("AI is analyzing table structure to create a transformation plan...")
        response = client.chat.completions.create(
            model=config.GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        plan = json.loads(response.choices[0].message.content)
        logger.info(f"AI successfully generated a '{plan.get('format_type')}' format plan.")
        return plan
    except Exception as e:
        logger.error(f"An error occurred with the Groq API call for planning: {e}")
        return None