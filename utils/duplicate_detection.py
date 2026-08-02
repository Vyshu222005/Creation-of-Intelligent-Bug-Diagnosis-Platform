"""
Duplicate Detection Agent
Milestone 3
"""

import ollama


def find_duplicate_bugs(bug_report, similar_bugs):

    try:

        # ----------------------------------------
        # Build Historical Context
        # ----------------------------------------

        history = ""

        for i, bug in enumerate(similar_bugs, start=1):

            history += f"""
Historical Bug {i}

Description:
{bug.get('description', '')}

Severity:
{bug.get('severity', '')}

Similarity:
{bug.get('similarity', 0)}%

"""

        # ----------------------------------------
        # Prompt
        # ----------------------------------------

        prompt = f"""
You are an experienced Software Defect Analyst.

Analyze the following bug report and compare it with the historical bugs.

Current Bug

{bug_report}

Historical Bugs

{history}

For every matching duplicate return ONLY:

Duplicate:
Similarity:
Resolution Summary:
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

        duplicates = []

        current = {}

        history_index = 0

        # ----------------------------------------
        # Parse Ollama Response
        # ----------------------------------------

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if lower.startswith("duplicate"):

                if current:
                    duplicates.append(current)

                if history_index < len(similar_bugs):

                    current = {

                        "bug":
                        similar_bugs[history_index]["description"][:120] + "...",

                        "similarity":
                        f"{similar_bugs[history_index]['similarity']}%",

                        "resolution":
                        ""

                    }

                    history_index += 1

            elif lower.startswith("similarity"):

                if ":" in line:

                    current["similarity"] = line.split(":", 1)[1].strip()

            elif lower.startswith("resolution"):

                if ":" in line:

                    current["resolution"] = line.split(":", 1)[1].strip()

        if current:

            duplicates.append(current)

        # ----------------------------------------
        # If Ollama returns nothing
        # ----------------------------------------

        if len(duplicates) == 0:

            for bug in similar_bugs[:3]:

                duplicates.append({

                    "bug":
                    bug["description"][:120] + "...",

                    "similarity":
                    f"{bug['similarity']}%",

                    "resolution":
                    "Compare this historical bug with the current issue and review the previous implementation before applying a fix."

                })

        # ----------------------------------------
        # Fill Missing Resolution Only
        # ----------------------------------------

        for duplicate in duplicates:

            if duplicate["resolution"] == "":

                duplicate["resolution"] = (

                    "Compare this historical bug with the current issue "
                    "and review the previous implementation before applying a fix."

                )

        return duplicates

    except Exception:

        fallback = []

        for bug in similar_bugs:

            fallback.append({

                "bug":
                bug.get("description", "")[:120] + "...",

                "similarity":
                f"{bug.get('similarity', 0)}%",

                "resolution":
                "Review historical fixes and compare the implementation."

            })

        return fallback