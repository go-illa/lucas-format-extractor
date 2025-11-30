import pandas as pd
import logging
from typing import Dict, List, Union, Tuple
from collections import defaultdict

from etl.mapping import get_sku_mapping, get_location_mapping

pd.set_option('future.no_silent_downcasting', True)

# Set up logging
logger = logging.getLogger(__name__)


def _apply_mapping_and_get_status(client_code: str, mapping_dict: Union[defaultdict, dict], is_dict: bool = False) -> Tuple[str, str]:
    """Applies mapping and returns the new code and status."""
    if not client_code or pd.isna(client_code):
        return client_code, "Missing Raw Data"

    if is_dict:
        f_code = mapping_dict.get(str(client_code))
        if f_code:
            return f_code, "Mapped"
        else:
            return client_code, "Missing Mapping"
    else: # defaultdict
        f_codes = mapping_dict.get(str(client_code), [])
        if len(f_codes) == 1:
            return f_codes[0], "Mapped"
        elif len(f_codes) > 1:
            logger.warning(f"Ambiguous mapping for client code '{client_code}'. Found {len(f_codes)} options: {f_codes}")
            return client_code, f"Ambiguous ({', '.join(map(str, f_codes))})"
        else:
            return client_code, "Missing Mapping"


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

    # After mapping, fill in constant values from the schema
    for field in target_schema:
        if 'const' in field and field['name'] in target_columns:
            standard_df[field['name']] = field['const']

    # --- Apply FD Code Mappings ---
    logger.info("Applying FD code mappings...")
    sku_map = get_sku_mapping()
    loc_map = get_location_mapping()

    if 'Sku' in standard_df.columns and not sku_map.keys().__len__==0:
        res = standard_df['Sku'].apply(lambda x: _apply_mapping_and_get_status(x, sku_map, is_dict=True))
        standard_df['Sku'], standard_df['Sku Mapping Status'] = zip(*res)
        
    if 'Location ID' in standard_df.columns and not loc_map.keys().__len__==0:
        res = standard_df['Location ID'].apply(lambda x: _apply_mapping_and_get_status(x, loc_map))
        standard_df['Location ID'], standard_df['Location ID Mapping Status'] = zip(*res)

    # Ensure all target columns are present
    all_cols = target_columns + ['Sku Mapping Status', 'Location ID Mapping Status']
    final_df = standard_df.reindex(columns=all_cols)

    return final_df


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

    # This assumes the unpivoted column (`var_name`) contains the client SKU
    # And one of the id_vars contains the client Location ID.
    # We rename them to 'Sku' and 'Location ID' for mapping.
    # This might need adjustment based on the actual LLM-provided action.
    if var_name not in final_df.columns:
         final_df[var_name] = unpivoted[var_name]
    
    final_df = final_df.rename(columns={var_name: 'Sku'})


    final_df[value_name] = unpivoted[value_name].astype(int)

    target_columns = [field['name'] for field in target_schema if field.get('name')]
    
    # After unpivoting, fill in constant values from the schema
    for field in target_schema:
        if 'const' in field and field['name'] in target_columns:
            final_df[field['name']] = field['const']
            
    # --- Apply FD Code Mappings ---
    logger.info("Applying FD code mappings to unpivoted data...")
    sku_map = get_sku_mapping()
    loc_map = get_location_mapping()

    if 'Sku' in final_df.columns and not sku_map.keys().__len__==0:
        res = final_df['Sku'].apply(lambda x: _apply_mapping_and_get_status(x, sku_map, is_dict=True))
        final_df['Sku'], final_df['Sku Mapping Status'] = zip(*res)
        
    if 'Location ID' in final_df.columns and not loc_map.keys().__len__==0:
        res = final_df['Location ID'].apply(lambda x: _apply_mapping_and_get_status(x, loc_map))
        final_df['Location ID'], final_df['Location ID Mapping Status'] = zip(*res)
        
    # Ensure all target columns are present
    all_cols = target_columns + ['Sku Mapping Status', 'Location ID Mapping Status']
    final_df = final_df.reindex(columns=all_cols)

    return final_df
