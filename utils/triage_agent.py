from ollama import chat
import json


def triage_bug(bug_report):
    prompt = f"""
You are an expert Software Bug Triage Agent.

Analyze the following bug report.

Predict:
1. Severity (Critical/High/Medium/Low)
2. Priority (P1/P2/P3/P4)
3. Affected Component
4. Confidence Score (0-100)
5. Reasoning

Return ONLY valid JSON in this format:

{{
  "severity": "",
  "priority": "",
  "component": "",
  "confidence": 0,
  "reasoning": ""
}}

Bug Report:
{bug_report}
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

    try:
        return json.loads(result)
    except:
        return {
            "severity": "Unknown",
            "priority": "Unknown",
            "component": "Unknown",
            "confidence": 0,
            "reasoning": result
        }


if __name__ == "__main__":
    sample = "Application crashes when user clicks Login button"

    print(triage_bug(sample))