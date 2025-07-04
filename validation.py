import re
from datetime import datetime

def validate_positive_int(value):
    return isinstance(value, int) and value > 0

def sanitize_string(value, max_length=255):
    if not isinstance(value, str):
        return None

    clean = value.strip()

    # Remove control characters (except newline/tab if desired)
    clean = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', clean)

    clean = re.sub(r'<[^>]+>', '', clean)

    if 0 < len(clean) <= max_length:
        return clean
    return None

def validate_number(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

# MM/DD/YYYY format, allows leading zeros
date_regex_mdy = re.compile(r"^(0[1-9]|1[0-2])/([0-2][0-9]|3[01])/(\d{4})$")

def validate_date(date_string):
    """
    Validates that the input is a proper date in MM/DD/YYYY format.
    Returns True if valid, False otherwise.
    """
    if not isinstance(date_string, str):
        print("failed isinstance")
        return False

    if not date_regex_mdy.match(date_string):
        print("failed regex")
        return False

    try:
        datetime.strptime(date_string, "%m/%d/%Y")
        return True
    except ValueError:
        print("failed strptime")
        return False