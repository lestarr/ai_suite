import logging
import json
from enum import Enum
from pydantic import BaseModel
from typing import Any, Union
from pathlib import Path

class EnhancedJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Enum serialization and Pydantic models."""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, 'model_dump'):  # Handle Pydantic models
            return obj.model_dump()
        if hasattr(obj, 'dict'):  # Handle older Pydantic models
            return obj.dict()
        # Handle specific types that might be in your models
        if hasattr(obj, 'url'):  # Handle Url objects
            return str(obj.url)
        # Add a more generic fallback for objects
        try:
            return dict(obj)
        except (TypeError, ValueError):
            try:
                return str(obj)
            except Exception:
                return repr(obj)

def merge_extraction_results(dict1: dict, extr_model: type[BaseModel], logger: logging.Logger, source: str = None) -> dict:
    dict2 = None
    if extr_model:
        dict2 = extr_model.model_dump()
    return merge_json_results(dict1, dict2, logger, source)
    


def merge_json_results(dict1: dict, dict2: dict, logger: logging.Logger, source: str = None) -> dict:
    """Merge two dictionaries recursively, with special handling for lists and None values.
    
    Args:
        dict1: First dictionary (existing data with sources)
        dict2: Second dictionary (new data to be merged)
        logger: Logger instance
        source: Source identifier for the new data (dict2)
    
    Rules:
    1. If dict1 value is None, use dict2 value
    2. If both values are lists, combine them uniquely
    3. If both values are dicts, merge recursively
    4. Otherwise keep dict1 value
    """
    logger.info("Merging results...")
    
    if not dict1:
        if not dict2:
            return {}
        return dict2
    
    # Create a copy of dict1 to avoid modifying the original
    result = dict1.copy()
    if not dict2:
        return result
    
    for key, value2 in dict2.items():
        # If key doesn't exist in result or its value is None
        if key not in result or result[key] is None:
            # Handle different types of values
            if isinstance(value2, dict):
                # Add source to dictionary
                value2 = {**value2, 'source': source}
            elif isinstance(value2, list) and value2 and isinstance(value2[0], dict):
                # Add source to each dictionary in list
                value2 = [{**item, 'source': source} for item in value2]
            result[key] = value2
            logger.debug(f"Updated field '{key}' with value from new data")
            
        else:
            value1 = result[key]
            
            # If both values are lists
            if isinstance(value1, list) and isinstance(value2, list):
                # Handle lists of dictionaries
                if value2 and isinstance(value2[0], dict):
                    # Check if we're dealing with content-based or target_group-based dictionaries
                    if all('content' in item for item in value1 + value2):
                        # Convert content to string if it's not hashable (like a list)
                        # and normalize to lowercase
                        existing_contents = {
                            (json.dumps(item['content']).lower() if isinstance(item['content'], (list, dict))
                            else str(item['content']).lower())
                            for item in value1
                        }
                        new_items = [
                            {**item, 'source': source} 
                            for item in value2 
                            if (json.dumps(item['content']).lower() if isinstance(item['content'], (list, dict))
                                else str(item['content']).lower()) not in existing_contents
                        ]
                    elif all('target_group' in item for item in value1 + value2):
                        # Handle target_group comparison without lowercase normalization
                        existing_target_groups = {
                            item['target_group'] for item in value1
                        }
                        new_items = [
                            {**item, 'source': source} 
                            for item in value2 
                            if item['target_group'] not in existing_target_groups
                        ]
                    else:
                        # Regular dictionary list handling
                        new_items = [{**item, 'source': source} for item in value2 if item not in value1]
                else:
                    new_items = [item for item in value2 if item not in value1]
                
                if new_items:
                    result[key].extend(new_items)
                    logger.debug(f"Added {len(new_items)} new items to list in field '{key}'")
                    
            # If both values are dictionaries, merge recursively
            elif isinstance(value1, dict) and isinstance(value2, dict):
                result[key] = merge_json_results(value1, value2, logger, source)
                logger.debug(f"Recursively merged dictionaries for field '{key}'")
                
            else:
                logger.debug(f"Kept existing value for field '{key}'")
    
    return result

def pretty_print_json(result: dict):    
    for key in result.keys():
        value = result[key]
                    
        # Format the value
        if isinstance(value, (dict, list)):
            formatted_value = json.dumps(value, indent=2, cls=EnhancedJSONEncoder)
            # Add indentation to each line
            formatted_value = "\n".join("  " + line for line in formatted_value.split("\n"))
            # add key here
            formatted_value = f"{key}:\n{formatted_value}"
            print(formatted_value)
        else:
            formatted_value = f"{key}: {value}"
            print(formatted_value)

def output_json(data, filename):
    """Write data to file in JSON format"""
    with open(filename, 'w', encoding='utf-8') as f:
        if isinstance(data, BaseModel):
            # Handle Pydantic model
            json.dump(data.model_dump(), f, indent=2, cls=EnhancedJSONEncoder)
        else:
            # Handle dictionary and other types
            json.dump(data, f, indent=2, cls=EnhancedJSONEncoder)

def save_json(data: Any, filepath: Union[str, Path], indent: int = 2) -> None:
    """
    Save data to a JSON file with proper encoding and error handling.
    
    Args:
        data: The data to save (dict, list, or any JSON-serializable object)
        filepath: Path where to save the JSON file
        indent: Number of spaces for indentation (default: 2)
    """
    filepath = Path(filepath)
    
    # Create directory if it doesn't exist
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, cls=EnhancedJSONEncoder, ensure_ascii=False)
    except Exception as e:
        raise Exception(f"Error saving JSON to {filepath}: {str(e)}")