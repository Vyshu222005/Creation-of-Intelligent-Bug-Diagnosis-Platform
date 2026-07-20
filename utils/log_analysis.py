import re

def analyze_log(log_text):

    result = {
        "exception_type": "Unknown",
        "failure_point": "Unknown",
        "line_number": "Unknown",
        "code_path": "General",
        "error_message": "Unknown"
    }

    # Convert multiple spaces/newlines into a single space
    text = re.sub(r'\s+', ' ', log_text)

    # ----------------------------
    # Exception Type
    # ----------------------------

    exception = re.search(
        r'([A-Za-z]+(?:Error|Exception))',
        text
    )

    if exception:
        result["exception_type"] = exception.group(1)

    # ----------------------------
    # File and Line Number
    # ----------------------------

    file_match = re.search(
        r'File\s+"([^"]+)"\s*,\s*line\s+(\d+)',
        text,
        re.IGNORECASE
    )

    if file_match:

        result["failure_point"] = file_match.group(1)

        result["line_number"] = file_match.group(2)

    # ----------------------------
    # Error Message
    # ----------------------------

    if exception:

        result["error_message"] = text[text.find(exception.group(1)):]

    # ----------------------------
    # Code Path Detection
    # ----------------------------

    lower = text.lower()

    if any(x in lower for x in ["login","signin","password","authentication"]):

        result["code_path"] = "Authentication"

    elif any(x in lower for x in ["database","mysql","sql"]):

        result["code_path"] = "Database"

    elif any(x in lower for x in ["upload","file","pdf","image"]):

        result["code_path"] = "File Upload"

    elif any(x in lower for x in ["api","endpoint","request"]):

        result["code_path"] = "API"

    elif any(x in lower for x in ["network","timeout","server"]):

        result["code_path"] = "Network"

    return result