import json
import logging
import os
import pandas as pd
from etl import extractor, planner, actions

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
        candidate_df = extractor.extract_main_table(client_file_path, sheet_name=sheet_name)

        if candidate_df is None or candidate_df.empty:
            logging.warning(f"No table found on sheet: '{sheet_name}'.")
            continue

        # Heuristic: A valid orders table should have a reasonable number of columns.
        if len(candidate_df.columns) < 3:
            logging.warning(f"Table on sheet '{sheet_name}' has only {len(candidate_df.columns)} columns. This is likely not the correct orders table. Trying next sheet.")
            continue

        # If we reach here, the table is considered valid based on the heuristic.
        logging.info(f"Successfully extracted a valid table from sheet: '{sheet_name}'")
        main_table_df = candidate_df
        break

    if main_table_df is None or main_table_df.empty:
        logging.error("Extraction failed: No valid data table with at least 3 columns found in any sheet. Aborting process.")
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
