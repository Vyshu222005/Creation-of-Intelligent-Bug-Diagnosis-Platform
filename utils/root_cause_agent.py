"""
Root Cause Analysis Agent
Milestone 3
"""

import ollama


def root_cause_analysis(bug_report, similar_bugs, log_analysis):

    try:

        # -------------------------------
        # Collect Similar Bug Evidence
        # -------------------------------
        evidence = ""

        for bug in similar_bugs:
            evidence += f"""
Description:
{bug.get('description', '')}

Severity:
{bug.get('severity', '')}

Similarity:
{bug.get('similarity', 0)}%
"""

        # -------------------------------
        # Extract Log Information
        # -------------------------------
        issues = log_analysis.get("issues", [])

        exception_type = "Unknown"
        failure_point = "Unknown"
        affected_code_path = "Unknown"

        log_text = ""

        if issues:

            first_issue = issues[0]

            exception_type = first_issue.get(
                "exception_type",
                "Unknown"
            )

            failure_point = first_issue.get(
                "failure_point",
                "Unknown"
            )

            affected_code_path = first_issue.get(
                "code_path",
                "Unknown"
            )

            for issue in issues:

                log_text += f"""
Exception:
{issue.get('exception_type', '')}

Failure Point:
{issue.get('failure_point', '')}

Code Path:
{issue.get('code_path', '')}

Root Cause:
{issue.get('root_cause', '')}

Error Message:
{issue.get('error_message', '')}
"""

        # -------------------------------
        # AI Prompt
        # -------------------------------
        prompt = f"""
You are a Senior Software Engineer.

Analyze the following software defect.

BUG REPORT

{bug_report}

LOG ANALYSIS

{log_text}

SIMILAR HISTORICAL BUGS

{evidence}

Determine:

1. Most probable root cause.
2. Confidence percentage.
3. Supporting historical evidence.

Return ONLY in this format.

Root Cause:
Confidence:
Supporting Evidence:
- Evidence 1
- Evidence 2
- Evidence 3
"""

        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        output = response["message"]["content"]

        root = ""
        confidence = "85%"
        support = []

        current_section = None

        for line in output.splitlines():

            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if lower.startswith("root cause"):

                root = (
                    line.split(":", 1)[1].strip()
                    if ":" in line else ""
                )

                current_section = "root"

            elif lower.startswith("confidence"):

                confidence = (
                    line.split(":", 1)[1].strip()
                    if ":" in line else "85%"
                )

                current_section = "confidence"

            elif lower.startswith("supporting evidence"):

                value = (
                    line.split(":", 1)[1].strip()
                    if ":" in line else ""
                )

                if value:
                    support.append(value)

                current_section = "support"

            elif line.startswith("-") or line.startswith("*"):

                if current_section == "support":
                    support.append(line[1:].strip())

        # -------------------------------
        # Default Values
        # -------------------------------
        if not root:

            root = (
                "The failure is most likely caused by improper input validation, "
                "application logic, or exception handling."
            )

        if not support:

            support = [

                "Historical bugs show similar behaviour.",

                "Log analysis indicates a matching failure pattern.",

                "Severity and similarity scores support this conclusion."

            ]

        # -------------------------------
        # Final Result
        # -------------------------------
        return {

            "exception_type": exception_type,

            "failure_point": failure_point,

            "affected_code_path": affected_code_path,

            "root_cause": root,

            "confidence": confidence,

            "evidence": support

        }

    except Exception as e:

        return {

            "exception_type": "Unknown",

            "failure_point": "Unknown",

            "affected_code_path": "Unknown",

            "root_cause":
                "Unable to determine the root cause from the available information.",

            "confidence": "0%",

            "evidence": [

                "Root cause analysis failed due to insufficient information or an internal processing error.",

                str(e)

            ]

        }