from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to access a dictionary value by key
    Usage: {{ mydict|get_item:key }}
    """
    if not dictionary:
        return None
    
    # Convert date objects to string if needed
    if hasattr(key, 'strftime'):
        key_str = key.strftime('%Y-%m-%d')  # Format date as string
        if key_str in dictionary:
            return dictionary[key_str]
            
    # Try direct access
    if key in dictionary:
        return dictionary[key]
    
    return None