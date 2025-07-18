def convert_addable_values_dict(obj):
    """Convert AddableValuesDict and nested objects to regular dict"""
    if hasattr(obj, 'dict'):
        return obj.dict()
    elif hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: convert_addable_values_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_addable_values_dict(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return obj
