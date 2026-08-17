"""
Log Analysis Agent
Intelligent Bug Diagnosis Platform
Milestone 2 / Milestone 3

Features:
- Exception detection
- Primary failure point detection
- Line number extraction
- Code path extraction
- Error message extraction
- Root cause identification
- Suggested fix
- Complete call stack
- ONE issue per exception
"""

import re


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# EXCEPTION DETECTION
# ============================================================

def detect_exception(log_text):

    patterns = [
        ("NullPointerException", r"\bNullPointerException\b"),
        ("AttributeError", r"\bAttributeError\b"),
        ("TypeError", r"\bTypeError\b"),
        ("ValueError", r"\bValueError\b"),
        ("KeyError", r"\bKeyError\b"),
        ("IndexError", r"\bIndexError\b"),
        ("SQLException", r"\b(?:SQLException|SQLSyntaxErrorException)\b"),
        ("IntegrityError", r"\bIntegrityError\b"),
        ("FileNotFoundError", r"\bFileNotFoundError\b"),
        ("PermissionError", r"\bPermissionError\b"),
        ("ConnectionError", r"\bConnectionError\b"),
        ("TimeoutError", r"\bTimeoutError\b"),
        ("HTTPError", r"\bHTTP(?:Error|Exception)\b"),
        ("ImportError", r"\bImportError\b"),
        ("ModuleNotFoundError", r"\bModuleNotFoundError\b"),
        ("RuntimeError", r"\bRuntimeError\b"),
        ("Exception", r"\bException\b"),
    ]

    for name, pattern in patterns:

        if re.search(
            pattern,
            log_text,
            re.IGNORECASE
        ):
            return name

    return "Unknown"


# ============================================================
# ERROR MESSAGE
# ============================================================

def extract_error_message(log_text, exception_type):

    lines = [
        line.strip()
        for line in log_text.splitlines()
        if line.strip()
    ]

    if not lines:
        return "No error message was provided."

    if exception_type != "Unknown":

        for line in lines:

            if re.search(
                rf"\b{re.escape(exception_type)}\b",
                line,
                re.IGNORECASE
            ):
                return line[:1000]

    for line in reversed(lines):

        if re.search(
            r"\b[A-Za-z_][A-Za-z0-9_]*(Error|Exception)\b",
            line
        ):
            return line[:1000]

    return lines[0][:1000]


# ============================================================
# STACK TRACE EXTRACTION
# ============================================================

def extract_stack_frames(log_text):

    frames = []

    # --------------------------------------------------------
    # Java stack trace
    # --------------------------------------------------------

    java_pattern = re.compile(
        r"^\s*at\s+"
        r"([\w.$]+)"
        r"\.([\w$<>]+)"
        r"\(([^:()]+):(\d+)\)",
        re.MULTILINE
    )

    for match in java_pattern.finditer(log_text):

        class_path = match.group(1)
        method = match.group(2)
        file_name = match.group(3)
        line_number = match.group(4)

        frames.append({
            "language": "Java",
            "class_path": class_path,
            "method": method,
            "file": file_name,
            "line_number": line_number,
            "failure_point":
                f"{class_path}.{method}()",
            "code_path":
                f"{class_path}.{method}({file_name}:{line_number})"
        })

    # --------------------------------------------------------
    # Python traceback
    # --------------------------------------------------------

    python_pattern = re.compile(
        r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+([^\s]+)'
    )

    for match in python_pattern.finditer(log_text):

        file_name = match.group(1)
        line_number = match.group(2)
        method = match.group(3)

        frames.append({
            "language": "Python",
            "class_path": "",
            "method": method,
            "file": file_name,
            "line_number": line_number,
            "failure_point":
                f"{method}()",
            "code_path":
                f"{file_name}:{line_number} in {method}()"
        })

    return frames


# ============================================================
# ROOT CAUSE
# ============================================================

def determine_root_cause(
    log_text,
    exception_type,
    error_message
):

    lower = log_text.lower()
    message_lower = error_message.lower()

    # --------------------------------------------------------
    # NullPointerException
    # --------------------------------------------------------

    if exception_type == "NullPointerException":

        if "username" in message_lower:

            return (
                "The username value is null before the "
                "authentication logic attempts to access it. "
                "The input should be validated before authentication."
            )

        if "user" in message_lower:

            return (
                "The required user object is null before it "
                "is accessed by the authentication flow."
            )

        if "session" in message_lower:

            return (
                "The application is attempting to access a "
                "null session object."
            )

        return (
            "A required object is null before it is accessed. "
            "The affected value should be validated or initialized "
            "before use."
        )

    # --------------------------------------------------------
    # Python AttributeError
    # --------------------------------------------------------

    if exception_type == "AttributeError":

        return (
            "The application attempted to access an attribute "
            "or method that is unavailable on the current object."
        )

    # --------------------------------------------------------
    # TypeError
    # --------------------------------------------------------

    if exception_type == "TypeError":

        return (
            "The application performed an operation using an "
            "incompatible or unexpected data type."
        )

    # --------------------------------------------------------
    # ValueError
    # --------------------------------------------------------

    if exception_type == "ValueError":

        return (
            "The application received a value with an invalid "
            "format or value for the expected operation."
        )

    # --------------------------------------------------------
    # KeyError
    # --------------------------------------------------------

    if exception_type == "KeyError":

        return (
            "The application attempted to access a dictionary "
            "or map key that does not exist."
        )

    # --------------------------------------------------------
    # IndexError
    # --------------------------------------------------------

    if exception_type == "IndexError":

        return (
            "The application attempted to access an index "
            "outside the valid collection range."
        )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    if exception_type in (
        "SQLException",
        "IntegrityError"
    ):

        return (
            "The application encountered a database operation "
            "failure. The query, connection, schema, constraints "
            "and supplied values should be reviewed."
        )

    # --------------------------------------------------------
    # File
    # --------------------------------------------------------

    if exception_type == "FileNotFoundError":

        return (
            "The application attempted to access a file or "
            "path that could not be found."
        )

    # --------------------------------------------------------
    # Permission
    # --------------------------------------------------------

    if exception_type == "PermissionError":

        return (
            "The application does not have sufficient permission "
            "to access the requested resource."
        )

    # --------------------------------------------------------
    # Network
    # --------------------------------------------------------

    if exception_type in (
        "ConnectionError",
        "TimeoutError"
    ):

        return (
            "The application could not complete a required "
            "network or external-service operation."
        )

    # --------------------------------------------------------
    # Import
    # --------------------------------------------------------

    if exception_type in (
        "ImportError",
        "ModuleNotFoundError"
    ):

        return (
            "A required Python module or dependency could not "
            "be imported successfully."
        )

    # --------------------------------------------------------
    # Generic null detection
    # --------------------------------------------------------

    if "null" in lower:

        return (
            "The failure appears to involve a null or missing "
            "value that was used without sufficient validation."
        )

    return (
        "The submitted log indicates an application runtime "
        "failure. The exception and primary failure point "
        "should be reviewed together."
    )


# ============================================================
# SUGGESTED FIX
# ============================================================

def determine_fix(exception_type):

    fixes = {

        "NullPointerException":
            "Validate the object or value for null before accessing it.",

        "AttributeError":
            "Validate the object before accessing the requested attribute or method.",

        "TypeError":
            "Validate input types before performing the operation.",

        "ValueError":
            "Validate and sanitize the input value before processing.",

        "KeyError":
            "Check that the required key exists before accessing it.",

        "IndexError":
            "Validate the collection length before accessing the requested index.",

        "SQLException":
            "Review the SQL query, database connection, schema and constraints.",

        "IntegrityError":
            "Check database constraints and validate the values before insertion or update.",

        "FileNotFoundError":
            "Verify the file path and ensure the required file exists.",

        "PermissionError":
            "Verify file, folder or service permissions.",

        "ConnectionError":
            "Check network connectivity and service availability.",

        "TimeoutError":
            "Review timeout configuration and external service availability.",

        "ImportError":
            "Verify that the required dependency is installed and correctly imported.",

        "ModuleNotFoundError":
            "Install the missing dependency and verify the Python environment.",

        "RuntimeError":
            "Review the runtime failure and reproduce the issue with detailed logging."
    }

    return fixes.get(
        exception_type,
        "Review the exception, failure point and affected code path."
    )


# ============================================================
# MAIN LOG ANALYSIS
# ============================================================

def analyze_log(log_text):

    log_text = clean_text(log_text)

    # --------------------------------------------------------
    # Empty log
    # --------------------------------------------------------

    if not log_text:

        return {
            "issues": [{
                "exception_type": "Unknown",
                "failure_point": "Not identified",
                "line_number": "-",
                "code_path": "-",
                "error_message":
                    "No log information was provided.",
                "root_cause":
                    "Insufficient log information was provided.",
                "severity": "Low",
                "suggested_fix":
                    "Paste a valid error message or stack trace.",
                "call_stack": []
            }],
            "summary":
                "No application log was provided.",
            "call_stack": []
        }

    # --------------------------------------------------------
    # Detect exception
    # --------------------------------------------------------

    exception_type = detect_exception(log_text)

    # --------------------------------------------------------
    # Error message
    # --------------------------------------------------------

    error_message = extract_error_message(
        log_text,
        exception_type
    )

    # --------------------------------------------------------
    # Stack frames
    # --------------------------------------------------------

    frames = extract_stack_frames(log_text)

    # --------------------------------------------------------
    # Root cause
    # --------------------------------------------------------

    root_cause = determine_root_cause(
        log_text,
        exception_type,
        error_message
    )

    # --------------------------------------------------------
    # Suggested fix
    # --------------------------------------------------------

    suggested_fix = determine_fix(
        exception_type
    )

    # --------------------------------------------------------
    # ONE issue only
    # --------------------------------------------------------

    if frames:

        primary = frames[0]

        issue = {
            "exception_type":
                exception_type,

            "failure_point":
                primary["failure_point"],

            "line_number":
                primary["line_number"],

            "code_path":
                primary["code_path"],

            "error_message":
                error_message,

            "root_cause":
                root_cause,

            "severity":
                "High"
                if exception_type != "Unknown"
                else "Medium",

            "suggested_fix":
                suggested_fix,

            "call_stack":
                frames
        }

    else:

        issue = {
            "exception_type":
                exception_type,

            "failure_point":
                "Not identified",

            "line_number":
                "-",

            "code_path":
                "-",

            "error_message":
                error_message,

            "root_cause":
                root_cause,

            "severity":
                "High"
                if exception_type != "Unknown"
                else "Medium",

            "suggested_fix":
                suggested_fix,

            "call_stack":
                []
        }

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = (
        f"Detected {exception_type}. "
        f"Primary failure point identified from "
        f"{len(frames)} stack-trace frame(s)."
    )

    return {
        "issues": [issue],
        "summary": summary,
        "call_stack": frames
    }


# ============================================================
# COMPATIBILITY FUNCTIONS
# ============================================================

def analyze_logs(log_text):
    return analyze_log(log_text)


def log_analysis(log_text):
    return analyze_log(log_text)


def analyze_log_file(log_text):
    return analyze_log(log_text)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sample = """
java.lang.NullPointerException: Cannot invoke "String.equals(Object)" because "username" is null
    at com.necn.auth.AuthenticationService.authenticate(AuthenticationService.java:45)
    at com.necn.controller.LoginController.login(LoginController.java:28)
    at com.necn.service.LoginService.processLogin(LoginService.java:72)
    at org.springframework.web.servlet.FrameworkServlet.doPost(FrameworkServlet.java:1014)
"""

    result = analyze_log(sample)

    print("\n========== LOG ANALYSIS ==========")

    print("\nSummary:")
    print(result["summary"])

    issue = result["issues"][0]

    print("\nException:")
    print(issue["exception_type"])

    print("\nFailure Point:")
    print(issue["failure_point"])

    print("\nLine:")
    print(issue["line_number"])

    print("\nCode Path:")
    print(issue["code_path"])

    print("\nError:")
    print(issue["error_message"])

    print("\nRoot Cause:")
    print(issue["root_cause"])

    print("\nSuggested Fix:")
    print(issue["suggested_fix"])

    print("\nCall Stack:")

    for frame in result["call_stack"]:
        print(
            " -",
            frame["code_path"]
        )