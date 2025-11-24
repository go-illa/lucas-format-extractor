import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
from collections import defaultdict

load_dotenv()
logger = logging.getLogger(__name__)

def _get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_sku_mapping():
    """
    Fetches the client SKU to FD SKU mapping from the database, ensuring one-to-one mapping.

    Returns:
        dict: A dictionary mapping a client_sku_code to a single fd_sku_code.
    """
    conn = _get_db_connection()
    if not conn:
        return {}

    sku_mapping = {}
    query = """
        SELECT DISTINCT ON (client_sku_code) 
            client_sku_code, 
            fd_sku_code 
        FROM products 
        WHERE client_sku_code IS NOT NULL AND fd_sku_code IS NOT NULL
        ORDER BY client_sku_code, fd_sku_code;
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            for row in cur.fetchall():
                sku_mapping[row['client_sku_code']] = row['fd_sku_code']
        logger.info(f"Loaded {len(sku_mapping)} unique client SKU mappings.")
    except Exception as e:
        logger.error(f"Error fetching SKU mapping: {e}")
    finally:
        conn.close()
    return sku_mapping

def get_location_mapping():
    """
    Fetches the client location code to FD location code mapping from the database.

    Returns:
        defaultdict: A dictionary mapping a client_code to a list of fd_codes.
    """
    conn = _get_db_connection()
    if not conn:
        return defaultdict(list)
        
    location_mapping = defaultdict(list)
    query = """
        SELECT 
            ms.supplier_code AS client_code,
            m.generated_code AS fd_code
        FROM merchants m
        JOIN merchant_suppliers ms ON m.id = ms.merchant_id
        WHERE ms.supplier_code IS NOT NULL AND m.generated_code IS NOT NULL;
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            for row in cur.fetchall():
                location_mapping[row['client_code']].append(row['fd_code'])
        logger.info(f"Loaded {len(location_mapping)} client location mappings.")
    except Exception as e:
        logger.error(f"Error fetching location mapping: {e}")
    finally:
        conn.close()
    return location_mapping
