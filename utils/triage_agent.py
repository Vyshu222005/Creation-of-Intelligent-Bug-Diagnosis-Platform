import re

def triage_bug(bug_report):
    """
    Analyze a bug report and predict:
    - Severity
    - Priority
    - Component
    - Confidence
    - Reasoning
    """

    text = bug_report.lower()

    # Default values
    severity = "Low"
    priority = "P4"
    component = "General"
    confidence = 0.70
    reason = "No major issue detected."

    # -------- Severity Rules --------
    if any(word in text for word in ["crash", "fatal", "critical", "data loss"]):
        severity = "Critical"
        priority = "P1"
        confidence = 0.98
        reason = "Bug causes application crash or critical failure."

    elif any(word in text for word in ["exception", "error", "failed", "failure"]):
        severity = "High"
        priority = "P2"
        confidence = 0.94
        reason = "Bug affects core functionality."

    elif any(word in text for word in ["slow", "delay", "timeout"]):
        severity = "Medium"
        priority = "P3"
        confidence = 0.88
        reason = "Performance issue detected."

    # -------- Component Detection --------
    if any(word in text for word in ["login", "password", "authentication", "signin"]):
        component = "Authentication"

    elif any(word in text for word in ["database", "sql", "mysql"]):
        component = "Database"

    elif any(word in text for word in ["api", "endpoint"]):
        component = "API"

    elif any(word in text for word in ["upload", "file"]):
        component = "File Upload"

    elif any(word in text for word in ["button", "ui", "screen", "page"]):
        component = "User Interface"

    result = {
        "severity": severity,
        "priority": priority,
        "component": component,
        "confidence": confidence,
        "reasoning": reason
    }

    return result


# Test the file
if __name__ == "__main__":
    sample = "Application crashes when user clicks login button."

    result = triage_bug(sample)

    print(result)