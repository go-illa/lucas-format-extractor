import json
import logging
import os
import pandas as pd
from etl import extractor, planner, actions

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_action(action_name):
    """Maps action name to a function."""
    action_map = {
        "apply_direct_mapping": actions.apply_direct_mapping,
        "unpivot_wide_to_long": actions.unpivot_wide_to_long,
    }
    return action_map.get(action_name)

def process_client_file(client_file_path: str, schema_file_path: str, output_excel_path: str):
    """
    Executes the full ETL pipeline for a given client file and schema.
    It will try to find the relevant data by iterating through all sheets in the Excel file.
    """
    # --- 1. Load Inputs ---
    try:
        with open(schema_file_path, 'r') as f:
            target_schema = json.load(f)
        logging.info(f"Successfully loaded target schema from {schema_file_path}")
    except Exception as e:
        logging.error(f"Failed to load or parse schema file: {e}")
        return

    # --- 2. Execute ETL Pipeline ---
    try:
        xls = pd.ExcelFile(client_file_path)
        sheet_names = xls.sheet_names
    except Exception as e:
        logging.error(f"Could not open Excel file to get sheet names: {e}")
        return

    main_table_df = None
    for sheet_name in sheet_names:
        logging.info(f"Attempting extraction from sheet: '{sheet_name}'")
        main_table_df = extractor.extract_main_table(client_file_path, sheet_name=sheet_name)
        if main_table_df is not None and not main_table_df.empty:
            logging.info(f"Successfully extracted data from sheet: '{sheet_name}'")
            break  # Found a good sheet, so we can stop.
        else:
            logging.warning(f"No valid data extracted from sheet: '{sheet_name}'. Trying next sheet.")

    if main_table_df is None or main_table_df.empty:
        logging.error("Extraction failed for all sheets. Aborting process.")
        return

    action_details = planner.select_action_with_llm(main_table_df, target_schema)
    if not action_details:
        logging.error("Action selection failed. Aborting process.")
        return
    logging.info("AI Action Selected:\n" + json.dumps(action_details, indent=2))

    action_name = action_details.get("action")
    action_params = action_details.get("parameters")
    
    action_function = get_action(action_name)

    if not action_function:
        logging.error(f"Action '{action_name}' is not a valid action. Aborting process.")
        return

    try:
        # Add the DataFrame and schema to the parameters
        action_params['client_df'] = main_table_df
        action_params['target_schema'] = target_schema
        
        final_df = action_function(**action_params)
    except TypeError as e:
        logging.error(f"Error calling action '{action_name}': {e}. Check if the parameters from the LLM are correct.")
        return
    except Exception as e:
        logging.error(f"An unexpected error occurred during the '{action_name}' action: {e}")
        return

    if final_df is None or final_df.empty:
        logging.error("Transformation failed. No data to output.")
        return

    # --- 3. Save Output ---
    try:
        os.makedirs(os.path.dirname(output_excel_path), exist_ok=True)
        final_df.to_excel(output_excel_path, index=False)
        logging.info(f"🎉 Success! Transformed data saved to {output_excel_path}")
    except Exception as e:
        logging.error(f"Failed to save the final excel file: {e}")


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # --- Configurable Paths ---
    INPUT_FILENAME = 'real-elano-data.xlsx'
    SCHEMA_FILENAME = 'lucas_target_schema.json'
    
    # --- Dynamic Path Construction ---
    INPUT_FILE_PATH = os.path.join(BASE_DIR, 'input', INPUT_FILENAME)
    SCHEMA_FILE_PATH = os.path.join(BASE_DIR, 'schema', SCHEMA_FILENAME)
    
    # Generate the output path based on the input filename
    input_basename, input_ext = os.path.splitext(os.path.basename(INPUT_FILE_PATH))
    OUTPUT_FILENAME = f"{input_basename}_transformed.xlsx"
    OUTPUT_FILE_PATH = os.path.join(BASE_DIR, 'output', OUTPUT_FILENAME)
    
    os.makedirs(os.path.dirname(SCHEMA_FILE_PATH), exist_ok=True)
    if not os.path.exists(SCHEMA_FILE_PATH):
        print("Schema file not found. Creating a default schema file...")
        with open(SCHEMA_FILE_PATH, 'w') as f:
            json.dump([
                {"name": "OrderID", "description": "The unique identifier for the customer's order."},
                {"name": "OrderDate", "description": "The date the order was placed, format DD/MM/YYYY."},
                {"name": "Sku ID", "description": "The unique code for the product or material."},
                {"name": "Quantity", "description": "The number of units for the given Sku ID."}
            ], f, indent=2)
        logging.info(f"Created a default schema file at {SCHEMA_FILE_PATH}")

    if not os.path.exists(INPUT_FILE_PATH):
         logging.error(f"FATAL: Input file not found at '{INPUT_FILE_PATH}'.")
         logging.warning("Please place your client's Excel file in the '/input/' directory and update the path in main.py")
    else:
        process_client_file(
            client_file_path=INPUT_FILE_PATH,
            schema_file_path=SCHEMA_FILE_PATH,
            output_excel_path=OUTPUT_FILE_PATH
        )

        