import pandas as pd
import json
import logging
from groq import Groq
import config
from typing import Union
import os

# Set up logging
logger = logging.getLogger(__name__)

def _load_prompt_template(filename: str) -> str:
    """Loads a prompt template from the prompts directory."""
    path = os.path.join(config.PROMPT_TEMPLATE_DIR, filename)
    with open(path, 'r') as f:
        return f.read()

def _find_header_row_index_with_llm(raw_df: pd.DataFrame) -> Union[int, None]:
    """Uses an LLM to find the index of the header row in a messy dataframe."""
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
        
    client = Groq(api_key=config.GROQ_API_KEY)
    sample_text = raw_df.head(20).to_string(index=True, header=False)
    
    prompt_template = _load_prompt_template('find_header_prompt.txt')
    prompt = prompt_template.format(sample_text=sample_text)
    
    try:
        logger.info("AI is scanning for the main table header...")
        response = client.chat.completions.create(
            model=config.GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get('header_row_index')
    except Exception as e:
        logger.error(f"AI failed to find header row: {e}")
        return None

def extract_main_table(file_path: str) -> Union[pd.DataFrame, None]:
    """
    Reads an Excel file, uses an LLM to find the main table, and returns it as a clean DataFrame.
    """
    logger.info(f"Reading raw data from {file_path}...")
    try:
        raw_df = pd.read_excel(file_path, header=None, engine='openpyxl')
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        return None
    
    header_row_index = _find_header_row_index_with_llm(raw_df)
    
    if header_row_index is None or not isinstance(header_row_index, int):
        logger.error("AI could not reliably locate the main data table header.")
        return None
        
    logger.info(f"AI identified the main table header at row {header_row_index + 1}.")
    
    table_candidate = raw_df.iloc[header_row_index:].copy().reset_index(drop=True)
    header_series = table_candidate.iloc[0]
    columns_to_keep = header_series.notna()
    
    clean_df = table_candidate.loc[:, columns_to_keep]
    clean_df.columns = clean_df.iloc[0].astype(str).str.strip()
    clean_df = clean_df.iloc[1:].reset_index(drop=True)
    clean_df.dropna(how='all', inplace=True)
    
    logger.info(f"Successfully extracted main table with {len(clean_df)} rows and {len(clean_df.columns)} columns.")
    return clean_df