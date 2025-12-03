import json
import logging
import os
import json
import logging
import os
from etl.pipeline import process_client_file

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # --- Configurable Paths ---
    INPUT_FILENAME = 'سلاسل فرونت دور 3-12-2025.xlsx'
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

        