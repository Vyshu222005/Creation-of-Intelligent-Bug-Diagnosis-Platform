"""
Duplicate Detection Agent
Milestone 3 + Milestone 4
"""

import ollama
import json


from utils.knowledge_base_growth import search_verified_bugs


# ============================================================
# Configuration
# ============================================================

DUPLICATE_THRESHOLD = 70.0


# ============================================================
# Similarity Helper
# ============================================================

def get_similarity(bug):

    try:

        value = bug.get(
            "similarity",
            0
        )

        if isinstance(value, str):

            value = value.replace(
                "%",
                ""
            ).strip()

        return float(value)

    except Exception:

        return 0.0


# ============================================================
# Description Helper
# ============================================================

def get_description(bug):

    value = bug.get(
        "description",
        ""
    )

    if value is None:
        return ""

    value = str(value).strip()

    # Remove invalid descriptions
    if value.lower() in [
        "nan",
        "none",
        "null",
        "no bug description was provided."
    ]:

        return ""

    return value
# ============================================================
# Find Duplicate Bugs
# ============================================================

def find_duplicate_bugs(
    bug_report,
    similar_bugs
):

    try:

        bug_report = str(
            bug_report or ""
        ).strip()

        # ====================================================
        # Collect Original Historical Bugs
        # ====================================================

        candidates = []

        for bug in (
            similar_bugs or []
        ):

            description = get_description(
                bug
            )

            # Skip empty records
            if not description:
                continue

            candidates.append({

                "description":
                    description,

                "severity":
                    bug.get(
                        "severity",
                        "Unknown"
                    ),

                "similarity":
                    get_similarity(
                        bug
                    ),

                "resolution":
                    bug.get(
                        "resolution",
                        ""
                    ) or "",

                "root_cause":
                    bug.get(
                        "root_cause",
                        ""
                    ) or "",

                "component":
                    bug.get(
                        "component",
                        "Unknown"
                    ),

                "source":
                    bug.get(
                        "source",
                        "Historical Knowledge Base"
                    ),

                "bug_id":
                    bug.get(
                        "bug_id",
                        ""
                    )

            })


        # ====================================================
        # Search Verified Knowledge Base
        # ====================================================

        try:

            verified_bugs = search_verified_bugs(
                bug_report,
                top_k=5
            )

        except Exception as e:

            print(
                "Verified Knowledge Base Error:",
                e
            )

            verified_bugs = []


        # ====================================================
        # Add Verified Bugs
        # ====================================================

        for bug in verified_bugs:

            description = get_description(
                bug
            )

            if not description:
                continue

            candidates.append({

                "description":
                    description,

                "severity":
                    bug.get(
                        "severity",
                        "Unknown"
                    ),

                "similarity":
                    get_similarity(
                        bug
                    ),

                "resolution":
                    bug.get(
                        "resolution",
                        ""
                    ) or "",

                "root_cause":
                    bug.get(
                        "root_cause",
                        ""
                    ) or "",

                "component":
                    bug.get(
                        "component",
                        "Unknown"
                    ),

                "source":
                    "Verified Knowledge Base",

                "bug_id":
                    bug.get(
                        "bug_id",
                        ""
                    )

            })


        # ====================================================
        # Remove Duplicate Descriptions
        # ====================================================

        unique_bugs = []

        seen = set()

        for bug in candidates:

            key = bug[
                "description"
            ][:250].lower()

            if key in seen:
                continue

            seen.add(key)

            unique_bugs.append(
                bug
            )


        # ====================================================
        # Sort by Similarity
        # ====================================================

        unique_bugs.sort(
            key=get_similarity,
            reverse=True
        )


        # Keep top 10 candidates
        unique_bugs = unique_bugs[:10]


        # ====================================================
        # No Historical Bugs
        # ====================================================

        if not unique_bugs:

            return []


        # ====================================================
        # Continue in Part 3
        # ====================================================

        strong_matches = [

            bug

            for bug in unique_bugs

            if get_similarity(bug)
            >= DUPLICATE_THRESHOLD

        ][:5]


        # No strong enough match
        if not strong_matches:

            return []
                # ====================================================
        # Build Historical Context
        # ====================================================

        history = ""

        for i, bug in enumerate(
            strong_matches,
            start=1
        ):

            history += f"""
Historical Bug {i}

Bug ID:
{bug.get("bug_id", "")}

Description:
{bug.get("description", "")}

Severity:
{bug.get("severity", "Unknown")}

Similarity:
{get_similarity(bug):.2f}%

Component:
{bug.get("component", "Unknown")}

Root Cause:
{bug.get("root_cause", "")}

Previous Resolution:
{bug.get("resolution", "")}
"""


        # ====================================================
        # Ask Ollama to Verify True Duplicate
        # ====================================================

        prompt = f"""
You are a senior software defect analyst.

Determine whether any historical bug below is a TRUE
duplicate of the current bug.

Current Bug:
{bug_report}

Historical Bugs:
{history}

Rules:

1. Similarity alone does NOT prove duplication.
2. Compare the actual failure, component, exception,
   and underlying problem.
3. Do not mark unrelated bugs as duplicates.
4. Do not invent historical resolutions.
5. If there is no genuine duplicate, return exactly:

NO_DUPLICATE

If there is a genuine duplicate, return:

Duplicate: 1
Similarity: <percentage>
Resolution Summary: <existing resolution>

Do not use Markdown.
"""


        # ====================================================
        # Call Ollama
        # ====================================================

        try:

            response = ollama.chat(

                model="llama3.2",

                messages=[

                    {
                        "role": "user",
                        "content": prompt
                    }

                ]

            )

            text = response[
                "message"
            ][
                "content"
            ].strip()

        except Exception as e:

            print(
                "Ollama Duplicate Detection Error:",
                e
            )

            # If Ollama fails, do not falsely
            # label a similar bug as duplicate.
            return []


        # ====================================================
        # No Duplicate
        # ====================================================

        if "NO_DUPLICATE" in text.upper():

            return []


        # ====================================================
        # Find Selected Historical Bugs
        # ====================================================

        selected_indices = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if lower.startswith(
                "duplicate:"
            ):

                value = line.split(
                    ":",
                    1
                )[1].strip()

                try:

                    index = int(
                        value
                    ) - 1

                    if (
                        0 <= index
                        < len(strong_matches)
                    ):

                        selected_indices.append(
                            index
                        )

                except ValueError:

                    pass


        # ====================================================
        # Ollama Did Not Select Any Bug
        # ====================================================

        if not selected_indices:

            return []
                # ====================================================
        # Build Final Duplicate Results
        # ====================================================

        duplicates = []

        for index in selected_indices:

            bug = strong_matches[index]

            similarity = get_similarity(
                bug
            )

            resolution = str(
                bug.get(
                    "resolution",
                    ""
                ) or ""
            ).strip()

            if not resolution:

                resolution = (
                    "No verified resolution is available. "
                    "Review the historical bug and compare "
                    "the implementation before applying a fix."
                )

            duplicates.append({

                "bug":
                    get_description(
                        bug
                    )[:200] + "...",

                "similarity":
                    f"{similarity:.2f}%",

                "resolution":
                    resolution,

                "bug_id":
                    bug.get(
                        "bug_id",
                        ""
                    ),

                "severity":
                    bug.get(
                        "severity",
                        "Unknown"
                    ),

                "component":
                    bug.get(
                        "component",
                        "Unknown"
                    ),

                "source":
                    bug.get(
                        "source",
                        "Historical Knowledge Base"
                    )

            })


        # ====================================================
        # Return Duplicates
        # ====================================================

        return duplicates


    # ========================================================
    # Exception Handler
    # ========================================================

    except Exception as e:

        print(
            "Duplicate Detection Error:",
            e
        )

        return []
    # ============================================================
# Test Duplicate Detection
# ============================================================

if __name__ == "__main__":

    sample_bug = """
    Login API throws NullPointerException.
    AuthenticationService.authenticate() fails because
    the user object is null.
    """

    sample_history = [
        {
            "bug_id": "101",
            "description": (
                "Authentication fails because the user object "
                "is null during login."
            ),
            "severity": "Critical",
            "similarity": 91.5,
            "resolution": (
                "Add a null check before accessing the user object."
            ),
            "root_cause": (
                "User object was not initialized."
            ),
            "component": "Authentication"
        },
        {
            "bug_id": "102",
            "description": (
                "HTML page has incorrect image border styling."
            ),
            "severity": "Low",
            "similarity": 20.5,
            "resolution": (
                "Update the CSS styling."
            ),
            "root_cause": (
                "Incorrect CSS rule."
            ),
            "component": "UI"
        }
    ]

    result = find_duplicate_bugs(
        sample_bug,
        sample_history
    )

    print(
        "\nDuplicate Detection Result:"
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )