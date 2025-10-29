import pandas as pd
import logging
from typing import Dict, List,Union

# Set up logging
logger = logging.getLogger(__name__)

def _apply_long_format_plan(client_df: pd.DataFrame, plan: List[Dict], target_schema: List[Dict]) -> pd.DataFrame:
    """Processes 'long' format files based on the mapping plan."""
    key_target_cols = ['OrderID', 'Sku ID', 'Customer ID', 'Shipment Number', 'Material']
    key_source_cols = [
        rule['source_column'] for rule in plan 
        if rule.get('target_column') in key_target_cols and rule.get('source_column') in client_df.columns
    ]
    if key_source_cols:
        client_df.dropna(subset=key_source_cols, how='all', inplace=True)

    target_columns = [field['name'] for field in target_schema if field.get('name')]
    standard_df = pd.DataFrame(columns=target_columns)
    
    for rule in plan:
        target_col = rule.get('target_column')
        source_col = rule.get('source_column')
        transform = rule.get('transformation_rule')
        
        if not all([target_col, transform]) or target_col not in target_columns:
            continue
            
        try:
            if transform == "direct_map" and source_col in client_df.columns:
                standard_df[target_col] = client_df[source_col]
            elif transform == "convert_to_DD/MM/YYYY" and source_col in client_df.columns:
                 standard_df[target_col] = pd.to_datetime(client_df[source_col], errors='coerce').dt.strftime('%d/%m/%Y')
        except Exception as e:
            logger.warning(f"Could not apply rule for target '{target_col}' from source '{source_col}': {e}")
            
    return standard_df[target_columns]

def _apply_wide_format_plan(client_df: pd.DataFrame, plan: Dict, target_schema: List[Dict]) -> pd.DataFrame:
    """Processes 'wide' format files by unpivoting them."""
    key_mappings = plan.get('key_column_mappings', [])
    key_source_cols = [mapping['source'] for mapping in key_mappings if mapping.get('source') in client_df.columns]
    
    if key_source_cols:
        client_df.dropna(subset=key_source_cols, how='all', inplace=True)
    
    product_cols = plan.get('product_quantity_columns', [])
    id_vars_sources = [mapping['source'] for mapping in key_mappings]
    id_cols_to_fill = [col for col in id_vars_sources if col in client_df.columns]
    client_df[id_cols_to_fill] = client_df[id_cols_to_fill].ffill()
    
    valid_product_cols = [col for col in product_cols if col in client_df.columns]
    if not valid_product_cols:
        logger.warning("No valid product columns found for unpivoting. Returning empty DataFrame.")
        return pd.DataFrame()
    
    unpivoted = client_df.melt(
        id_vars=id_cols_to_fill, 
        value_vars=valid_product_cols, 
        var_name="Sku ID", 
        value_name="Quantity"
    )
    unpivoted['Quantity'] = pd.to_numeric(unpivoted['Quantity'], errors='coerce')
    unpivoted = unpivoted.dropna(subset=['Quantity'])
    unpivoted = unpivoted[unpivoted['Quantity'] > 0].copy()

    final_df = pd.DataFrame()
    for mapping in key_mappings:
        target, source = mapping['target'], mapping['source']
        if source in unpivoted.columns:
            if 'Date' in target:
                final_df[target] = pd.to_datetime(unpivoted[source], errors='coerce').dt.strftime('%d/%m/%Y')
            else:
                final_df[target] = unpivoted[source]

    final_df['Sku ID'] = unpivoted['Sku ID'] 
    final_df['Quantity'] = unpivoted['Quantity'].astype(int)
    
    target_columns = [field['name'] for field in target_schema if field.get('name')]
    return final_df.reindex(columns=target_columns)

def apply_transformation_plan(client_df: pd.DataFrame, plan: Dict, target_schema: List[Dict]) -> Union[pd.DataFrame, None]:
    """
    Executes the transformation based on the AI-generated plan.
    This is Stage 3: The "Executor".
    """
    format_type = plan.get('format_type')
    mapping_plan = plan.get('mapping_plan')
    
    logger.info(f"Applying '{format_type}' transformation...")
    
    if format_type == 'long':
        return _apply_long_format_plan(client_df, mapping_plan, target_schema)
    elif format_type == 'wide':
        return _apply_wide_format_plan(client_df, mapping_plan, target_schema)
    else:
        logger.error(f"Unknown format type received from AI plan: '{format_type}'")
        return None