import re
from datetime import datetime, timedelta

# Updated Pattern: #YYYY-MM-DD# (No brackets)
DATE_TIME_PATTERN = r"#(.*?)#"

def is_formatted_datetime(val):
    """Checks if a string is wrapped in #...#."""
    if not isinstance(val, str):
        return False
    # Must start and end with # and have content
    return bool(re.match(r"^#.+?#$", val))

def parse_formatted_datetime(val):
    """
    Parses #YYYY-MM-DD HH:MM:SS# or #YYYY-MM-DD# into a datetime object.
    Returns None if parsing fails.
    """
    if not is_formatted_datetime(val):
        return None
    
    clean_val = re.findall(DATE_TIME_PATTERN, val)[0]
    
    # Try different formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%H:%M:%S",
        "%m %d %Y %H:%M:%S", # User requested format
        "%m %d %Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_val, fmt)
        except ValueError:
            continue
    return None

def format_as_datetime(dt):
    """Wraps a datetime object in #...#."""
    if not dt:
        return None
    # Check if it has a time component
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        return f"#{dt.strftime('%Y-%m-%d')}#"
    return f"#{dt.strftime('%Y-%m-%d %H:%M:%S')}#"

def add_to_datetime(val, delta, unit="Day"):
    """
    Adds a numeric delta to a formatted datetime based on the unit.
    """
    dt = parse_formatted_datetime(val)
    if not dt:
        return val
    
    try:
        if unit == "Milliseconds":
            new_dt = dt + timedelta(milliseconds=float(delta))
        elif unit == "Seconds":
            new_dt = dt + timedelta(seconds=float(delta))
        elif unit == "Minutes":
            new_dt = dt + timedelta(minutes=float(delta))
        elif unit == "Hours":
            new_dt = dt + timedelta(hours=float(delta))
        elif unit == "Week":
            new_dt = dt + timedelta(weeks=float(delta))
        elif unit == "Month":
            # Approximation: 30 days
            new_dt = dt + timedelta(days=float(delta) * 30)
        elif unit == "Year":
            # Approximation: 365 days
            new_dt = dt + timedelta(days=float(delta) * 365)
        else: # Default: Day
            new_dt = dt + timedelta(days=float(delta))
            
        return format_as_datetime(new_dt)
    except Exception as e:
        print(f"Error in add_to_datetime: {e}")
        return val

def subtract_from_datetime(val, delta, unit="Day"):
    """Subtracts a numeric delta from a formatted datetime."""
    try:
        return add_to_datetime(val, -float(delta), unit)
    except:
        return val

def compare_datetimes(val_a, val_b):
    """
    Compares two formatted datetime strings.
    Returns -1 if a < b, 1 if a > b, 0 if equal.
    Returns None if either is invalid.
    """
    dt_a = parse_formatted_datetime(val_a)
    dt_b = parse_formatted_datetime(val_b)
    
    if dt_a and dt_b:
        if dt_a < dt_b: return -1
        if dt_a > dt_b: return 1
        return 0
    return None

def evaluate_datetime_expression(val):
    """
    Evaluates a proprietary datetime expression: #base (+/-) delta unit#
    Example: #now + 1d#, #2024-01-01 - 2w#
    """
    if not is_formatted_datetime(val):
        return val
        
    content = val[1:-1].strip() # Strip #
    
    # 1. Parse Expression
    # Regex: (base) (op) (amount)(unit)
    # Simple split by space might work if strict: "now + 1d"
    
    # Handle "now"
    import re
    
    # Check for arithmetic
    match = re.search(r"(.+?)\s*([+-])\s*(\d*\.?\d+)([dhmswMy])", content)
    if match:
        base_str, op, amount, unit_char = match.groups()
        
        # Parse Base
        if base_str.lower() == "now":
            base_dt = datetime.now()
        else:
            # Re-wrap for parser
            base_dt = parse_formatted_datetime(f"#{base_str}#")
            
        if not base_dt: return val # Failed to parse base
        
        # Map Unit
        unit_map = {
            'd': 'Day', 'Day': 'Day',
            'h': 'Hours', 'Hour': 'Hours',
            'm': 'Minutes', 'Minute': 'Minutes',
            's': 'Seconds', 'Second': 'Seconds', 
            'w': 'Week', 'Week': 'Week',
            'M': 'Month', 'Month': 'Month',
            'y': 'Year', 'Year': 'Year'
        }
        unit = unit_map.get(unit_char, 'Day')
        
        delta = float(amount)
        if op == '-': delta = -delta
        
        # Calculate
        # We can reuse add_to_datetime but it takes string val.
        # Let's use internal logic or wrap base back to string.
        base_formatted = format_as_datetime(base_dt)
        return add_to_datetime(base_formatted, delta, unit)
        
    elif content.lower() == "now":
        return format_as_datetime(datetime.now())
        
    return val # Return original if no expression found (regular date)
