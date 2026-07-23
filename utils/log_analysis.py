from ollama import chat
import json
import re


def analyze_log(log_text):

    prompt = f"""
You are an expert Software Log Analysis Agent.

Analyze the following log.

Identify all errors, exceptions, warnings and failures.

For every issue, fill all fields.
Never leave any field empty.
If information is not explicitly available, infer the most likely answer.

Return ONLY valid JSON in this format:

{{
  "issues": [
    {{
      "exception_type": "NullPointerException",
      "failure_point": "LoginService.validateUser()",
      "line_number": "42",
      "code_path": "com.app.service.LoginService.java",
      "error_message": "User login failed",
      "root_cause": "The user object is null before validation.",
      "severity": "High",
      "suggested_fix": "Check for null before accessing the user object and initialize it properly."
    }}
  ]
}}

Log:
{log_text}
"""

    response = chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response["message"]["content"]

    print("\n===== OLLAMA RESPONSE =====")
    print(result)
    print("===========================\n")

    try:
        return json.loads(result)

    except json.JSONDecodeError:

        match = re.search(r"\{.*\}", result, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass

        return {
            "issues": [
                {
                    "exception_type": "Unknown",
                    "failure_point": "Unknown",
                    "line_number": "Unknown",
                    "code_path": "Unknown",
                    "error_message": result,
                    "root_cause": "LLM did not return valid JSON.",
                    "severity": "Unknown",
                    "suggested_fix": "Review the LLM response."
                }
            ]
        }