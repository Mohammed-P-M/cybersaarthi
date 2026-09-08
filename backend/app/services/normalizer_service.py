import re

def normalize_property(prop_type: str, raw_value: str) -> str:
    """
    Normalizes extracted entity values according to CyberSaarthi standards.
    """
    if not raw_value:
        return ""

    val = raw_value.strip()

    if prop_type == "PHONE":
        # Remove non-digits except leading plus
        digits = re.sub(r"[^\d]", "", val)
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]
        return digits

    elif prop_type == "UPI":
        return val.lower().replace(" ", "")

    elif prop_type == "TRANSACTION_ID":
        return val.upper().replace(" ", "")

    elif prop_type == "URL":
        clean = val.lower().strip()
        clean = re.sub(r"^https?://", "", clean)
        clean = re.sub(r"^www\.", "", clean)
        clean = clean.rstrip("/")
        return clean

    elif prop_type == "EMAIL":
        return val.lower().replace(" ", "")

    elif prop_type == "IFSC":
        return val.upper().replace(" ", "")

    elif prop_type == "AMOUNT":
        # Extract numbers and decimal
        clean = re.sub(r"[^\d.]", "", val)
        try:
            val_float = float(clean)
            return f"{val_float:.0f}" if val_float.is_integer() else f"{val_float:.2f}"
        except ValueError:
            return clean

    elif prop_type in ["LOCATION", "PERSON", "ORGANIZATION"]:
        return " ".join(val.title().split())

    elif prop_type == "DATE":
        return val.strip()

    elif prop_type == "TIME":
        return val.strip()

    elif prop_type == "SOCIAL_HANDLE":
        handle = val.lower().strip()
        if handle.startswith("@"):
            handle = handle[1:]
        return handle

    return val.strip()
