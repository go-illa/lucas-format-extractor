import pandas as pd
import logging
from typing import Dict, List, Union

pd.set_option('future.no_silent_downcasting', True)

# Set up logging
logger = logging.getLogger(__name__)


def apply_direct_mapping(client_df: pd.DataFrame, mapping: List[Dict], target_schema: List[Dict]) -> pd.DataFrame:
    """
    Processes a DataFrame with a direct mapping of columns.
    This action is for data that is already in a 'long' or tidy format.
    """
    key_target_cols = ['OrderID', 'Sku ID', 'Customer ID', 'Shipment Number', 'Material']
    key_source_cols = [
        rule['source_column'] for rule in mapping
        if rule.get('target_column') in key_target_cols and rule.get('source_column') in client_df.columns
    ]
    if key_source_cols:
        client_df.dropna(subset=key_source_cols, how='all', inplace=True)

    target_columns = [field['name'] for field in target_schema if field.get('name')]
    standard_df = pd.DataFrame(columns=target_columns)

    for rule in mapping:
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


def unpivot_wide_to_long(client_df: pd.DataFrame, id_vars: List[str], value_vars: List[str], var_name: str, value_name: str, key_mappings: List[Dict], target_schema: List[Dict]) -> pd.DataFrame:
    """
    Unpivots a wide DataFrame to a long format.
    """
    id_cols_to_fill = [col for col in id_vars if col in client_df.columns]
    client_df[id_cols_to_fill] = client_df[id_cols_to_fill].ffill()

    valid_product_cols = [col for col in value_vars if col in client_df.columns]
    if not valid_product_cols:
        logger.warning("No valid product columns found for unpivoting. Returning empty DataFrame.")
        return pd.DataFrame()

    unpivoted = client_df.melt(
        id_vars=id_cols_to_fill,
        value_vars=valid_product_cols,
        var_name=var_name,
        value_name=value_name
    )
    unpivoted[value_name] = pd.to_numeric(unpivoted[value_name], errors='coerce')
    unpivoted = unpivoted.dropna(subset=[value_name])
    unpivoted = unpivoted[unpivoted[value_name] > 0].copy()

    final_df = pd.DataFrame()
    for mapping in key_mappings:
        target, source = mapping['target'], mapping['source']
        if source in unpivoted.columns:
            if 'Date' in target:
                final_df[target] = pd.to_datetime(unpivoted[source], errors='coerce').dt.strftime('%d/%m/%Y')
            else:
                final_df[target] = unpivoted[source]

    final_df[var_name] = unpivoted[var_name]
    final_df[value_name] = unpivoted[value_name].astype(int)

    target_columns = [field['name'] for field in target_schema if field.get('name')]
    return final_df.reindex(columns=target_columns)
