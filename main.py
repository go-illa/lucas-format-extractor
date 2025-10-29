import json
import logging
import os
from etl import extractor, planner, transformer

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_client_file(client_file_path: str, schema_file_path: str, output_csv_path: str):
    """
    Executes the full ETL pipeline for a given client file and schema.
    
    Args:
        client_file_path (str): Path to the input client Excel file.
        schema_file_path (str): Path to the JSON file defining the target schema.
        output_csv_path (str): Path to save the final transformed CSV file.
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
    main_table_df = extractor.extract_main_table(client_file_path)
    if main_table_df is None or main_table_df.empty:
        logging.error("Extraction failed. Aborting process.")
        return

    plan = planner.generate_transformation_plan(main_table_df, target_schema)
    if not plan:
        logging.error("Plan generation failed. Aborting process.")
        return
    logging.info("AI Plan:\n" + json.dumps(plan, indent=2))

    final_df = transformer.apply_transformation_plan(main_table_df, plan, target_schema)
    if final_df is None or final_df.empty:
        logging.error("Transformation failed. No data to output.")
        return

    # --- 3. Save Output ---
    try:
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        final_df.to_excel(output_csv_path, index=False)
        logging.info(f"🎉 Success! Transformed data saved to {output_csv_path}")
    except Exception as e:
        logging.error(f"Failed to save the final excel file: {e}")


if __name__ == "__main__":

    # Define the input, schema, and output files for the ETL process.
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 1. SPECIFY THE CLIENT'S RAW DATA FILE
    #    Place the file in the '/input/' directory.
    INPUT_FILE_PATH = os.path.join(BASE_DIR, 'input', 'elano sample.xlsx')

    # 2. SPECIFY THE TARGET SCHEMA
    #    Place the schema definition in the '/schemas/' directory.
    SCHEMA_FILE_PATH = os.path.join(BASE_DIR, 'schema', 'lucas_target_schema.json')
    
    # 3. SPECIFY THE OUTPUT FILE PATH
    #    The processed file will be saved in the '/output/' directory.
    OUTPUT_FILE_PATH = os.path.join(BASE_DIR, 'output', 'elano_sample_TRANSFORMED.xlsx')
    
    # --- Create dummy schema file for first-time run if it doesn't exist ---
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

    # --- Check for input file before running ---
    if not os.path.exists(INPUT_FILE_PATH):
         logging.error(f"FATAL: Input file not found at '{INPUT_FILE_PATH}'.")
         logging.warning("Please place your client's Excel file in the '/input/' directory and update the path in main.py")
    else:
        # --- Run the main processing function ---
        process_client_file(
            client_file_path=INPUT_FILE_PATH,
            schema_file_path=SCHEMA_FILE_PATH,
            output_csv_path=OUTPUT_FILE_PATH
        )