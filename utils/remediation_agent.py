"""
Remediation Agent
Milestone 3
"""

import ollama


def generate_remediation(bug_report, root_cause, duplicate_results):

    try:

        duplicates = ""

        for bug in duplicate_results:

            duplicates += f"""
Bug:
{bug.get('bug', '')}

Similarity:
{bug.get('similarity', '')}

Resolution:
{bug.get('resolution', '')}

"""

        prompt = f"""
You are a Senior Software Architect.

Analyze the following bug and generate a remediation plan.

BUG REPORT:
{bug_report}

ROOT CAUSE:
{root_cause.get("root_cause", "")}

SIMILAR RESOLVED BUGS:
{duplicates}

Provide the response in the following format only.

Summary:
Immediate Fix:
- Step 1
- Step 2

Long Term Fix:
- Step 1
- Step 2

Testing:
- Test 1
- Test 2

Prevention:
- Prevention 1
- Prevention 2
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

        text = response["message"]["content"]

        remediation = {
            "summary": "",
            "steps": [],
            "testing": [],
            "prevention": []
        }

        current_section = None

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if lower.startswith("summary"):
                remediation["summary"] = (
                    line.split(":", 1)[1].strip()
                    if ":" in line else ""
                )
                current_section = "summary"

            elif lower.startswith("immediate fix"):
                value = line.split(":", 1)[1].strip() if ":" in line else ""
                if value:
                    remediation["steps"].append(value)
                current_section = "steps"

            elif lower.startswith("long term fix"):
                value = line.split(":", 1)[1].strip() if ":" in line else ""
                if value:
                    remediation["steps"].append(value)
                current_section = "steps"

            elif lower.startswith("testing"):
                value = line.split(":", 1)[1].strip() if ":" in line else ""
                if value:
                    remediation["testing"].append(value)
                current_section = "testing"

            elif lower.startswith("prevention"):
                value = line.split(":", 1)[1].strip() if ":" in line else ""
                if value:
                    remediation["prevention"].append(value)
                current_section = "prevention"

            elif line.startswith("-") or line.startswith("*"):

                value = line[1:].strip()

                if current_section == "steps":
                    remediation["steps"].append(value)

                elif current_section == "testing":
                    remediation["testing"].append(value)

                elif current_section == "prevention":
                    remediation["prevention"].append(value)

        if not remediation["summary"]:
            remediation["summary"] = (
                "The issue should be resolved by addressing the identified root cause, "
                "reviewing historical resolutions, and following software engineering best practices."
            )

        if not remediation["steps"]:
            remediation["steps"] = [
                "Validate all user inputs before processing.",
                "Add null and exception handling where required.",
                "Apply the necessary code fixes and verify the changes."
            ]

        if not remediation["testing"]:
            remediation["testing"] = [
                "Perform functional testing.",
                "Execute regression testing.",
                "Verify all affected modules after the fix."
            ]

        if not remediation["prevention"]:
            remediation["prevention"] = [
                "Add automated unit tests.",
                "Improve application logging and monitoring.",
                "Perform peer code reviews before deployment."
            ]

        return remediation

    except Exception:

        return {

            "summary":
                "The issue should be resolved by addressing the identified root cause and following software engineering best practices.",

            "steps": [

                "Validate all user inputs before processing.",

                "Add null and exception handling where required.",

                "Apply the necessary code fixes and verify the changes."

            ],

            "testing": [

                "Perform functional testing.",

                "Execute regression testing.",

                "Verify all affected modules after the fix."

            ],

            "prevention": [

                "Add automated unit tests.",

                "Improve application logging and monitoring.",

                "Perform peer code reviews before deployment."

            ]

        }