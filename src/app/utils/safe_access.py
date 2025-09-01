"""
Safe Access Utilities - Safely access nested attributes and dictionary keys
"""

from typing import Any, Optional

def safe_get_attribute(obj: Any, attr_path: str, default: Any = None) -> Any:
    """
    Safely get nested attributes from objects
    
    Args:
        obj: Object to get attribute from
        attr_path: Dot-separated path to attribute (e.g., 'customer.name.first')
        default: Default value if attribute not found
        
    Returns:
        Attribute value or default
    """
    try:
        attrs = attr_path.split('.')
        for attr in attrs:
            if obj is None:
                return default
            
            # Handle both objects and dictionaries
            if isinstance(obj, dict):
                obj = obj.get(attr, None)
            else:
                obj = getattr(obj, attr, None)
                
        return obj if obj is not None else default
    except:
        return default

def safe_get_dict_value(data: dict, key_path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values
    
    Args:
        data: Dictionary to get value from
        key_path: Dot-separated path to key
        default: Default value if key not found
        
    Returns:
        Dictionary value or default
    """
    try:
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
                
        return value
    except:
        return default
