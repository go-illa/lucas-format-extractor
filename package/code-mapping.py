import os
import psycopg2
from psycopg2.extras import RealDictCursor # Import this for dictionary output
from dotenv import load_dotenv
import json # Used to print the dictionary prettily

load_dotenv()

def verify_mappings():
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        
        # Use RealDictCursor to get results as {column: value}
        cur = conn.cursor(cursor_factory=RealDictCursor)

        print("-" * 50)
        print("1. VERIFYING PRODUCT SKU MAPPING")
        print("-" * 50)
        
        # Query 1: Check Products table
        # We select the specific columns you mentioned
        product_query = """
            SELECT fd_sku_code, client_sku_code 
            FROM products 
            WHERE fd_sku_code IS NOT NULL 
            LIMIT 1;
        """
        cur.execute(product_query)
        product_row = cur.fetchone()

        if product_row:
            print("✅ Sample Row from 'products':")
            print(json.dumps(product_row, indent=4))
            print(f"Mapping: FD '{product_row['fd_sku_code']}' <--> Client '{product_row['client_sku_code']}'")
        else:
            print("⚠️ No data found in 'products' table.")


        print("\n" + "-" * 50)
        print("2. VERIFYING LOCATION/MERCHANT MAPPING")
        print("-" * 50)

        # Query 2: JOIN merchants and merchant_suppliers
        # Assumption: merchant_suppliers table has a column 'merchant_id' linking to merchants.id
        location_query = """
            SELECT 
                m.generated_code AS fd_code, 
                ms.supplier_code AS client_code,
                m.id AS merchant_pk
            FROM merchants m
            JOIN merchant_suppliers ms ON m.id = ms.merchant_id
            LIMIT 1;
        """
        
        cur.execute(location_query)
        location_row = cur.fetchone()

        if location_row:
            print("✅ Sample Joined Row (merchants + merchant_suppliers):")
            print(json.dumps(location_row, indent=4))
            print(f"Mapping: FD '{location_row['fd_code']}' <--> Client '{location_row['client_code']}'")
        else:
            print("⚠️ No data found for the Merchant join.")
            print("Possible reasons: Tables are empty OR the Foreign Key isn't named 'merchant_id'.")

        cur.close()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_mappings()