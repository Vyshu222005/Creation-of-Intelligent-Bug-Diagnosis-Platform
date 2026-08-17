import os
import json
from collections import Counter
from datetime import datetime


# ============================================================
# Load all saved analysis reports
# ============================================================

def load_analysis_results(folder="analysis_results"):

    reports = []

    if not os.path.exists(folder):
        return reports

    for filename in os.listdir(folder):

        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(folder, filename)

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            reports.append(data)

        except Exception as e:

            print(
                f"Error reading {filename}: {e}"
            )

    return reports


# ============================================================
# Get Root Cause
# ============================================================

def get_root_cause(data):

    root = data.get(
        "root_cause",
        {}
    )

    if isinstance(root, dict):

        value = root.get(
            "root_cause",
            ""
        )

        if isinstance(value, list):

            return ", ".join(
                str(x) for x in value
            )

        return str(value)

    return str(root)


# ============================================================
# Get Component
# ============================================================

def get_component(data):

    triage = data.get(
        "triage",
        {}
    )

    if isinstance(triage, dict):

        component = (
            triage.get("component")
            or triage.get("affected_component")
            or triage.get("category")
        )

        if component:

            return str(component)

    ai_fix = data.get(
        "ai_fix",
        {}
    )

    if isinstance(ai_fix, dict):

        category = ai_fix.get(
            "category"
        )

        if category:

            return str(category)

    return "Unknown"


# ============================================================
# Get Exception Types
# ============================================================

def get_exceptions(data):

    exceptions = []

    log_analysis = data.get(
        "log_analysis",
        {}
    )

    if isinstance(log_analysis, dict):

        issues = log_analysis.get(
            "issues",
            []
        )

        if isinstance(issues, list):

            for issue in issues:

                if not isinstance(issue, dict):
                    continue

                exception_type = issue.get(
                    "exception_type",
                    ""
                )

                if exception_type:

                    exception_type = str(
                        exception_type
                    ).strip()

                    if (
                        exception_type
                        and exception_type != "-"
                    ):

                        exceptions.append(
                            exception_type
                        )

    return exceptions


# ============================================================
# Build Analytics Dashboard
# ============================================================

def build_analytics(
    folder="analysis_results"
):

    reports = load_analysis_results(
        folder
    )

    # Counters

    severity_counter = Counter()

    component_counter = Counter()

    root_cause_counter = Counter()

    exception_counter = Counter()

    date_counter = Counter()

    # ========================================================
    # Process Every Bug
    # ========================================================

    for data in reports:

        # ----------------------------------------------------
        # Severity
        # ----------------------------------------------------

        severity = str(
            data.get(
                "severity",
                "Unknown"
            )
        ).strip()

        if not severity:

            severity = "Unknown"

        severity_counter[
            severity
        ] += 1

        # ----------------------------------------------------
        # Component
        # ----------------------------------------------------

        component = get_component(
            data
        )

        if not component:

            component = "Unknown"

        component_counter[
            component
        ] += 1

        # ----------------------------------------------------
        # Root Cause
        # ----------------------------------------------------

        root_cause = get_root_cause(
            data
        )

        if (
            not root_cause
            or root_cause == "-"
        ):

            root_cause = "Unknown"

        root_cause_counter[
            root_cause
        ] += 1

        # ----------------------------------------------------
        # Exceptions
        # ----------------------------------------------------

        exceptions = get_exceptions(
            data
        )

        if exceptions:

            for exception in exceptions:

                exception_counter[
                    exception
                ] += 1

        else:

            exception_counter[
                "No Exception Detected"
            ] += 1

        # ----------------------------------------------------
        # Submission Date
        # ----------------------------------------------------

        submission_date = data.get(
            "submission_date",
            ""
        )

        if submission_date:

            try:

                date_obj = datetime.strptime(
                    submission_date,
                    "%d-%m-%Y %I:%M %p"
                )

                date_key = date_obj.strftime(
                    "%d-%m-%Y"
                )

            except Exception:

                date_key = str(
                    submission_date
                ).split()[0]

            date_counter[
                date_key
            ] += 1

    # ========================================================
    # Systemic Patterns
    # ========================================================

    systemic_patterns = []

    total_bugs = len(reports)

    if total_bugs > 0:

        # ----------------------------------------------------
        # Component Patterns
        # ----------------------------------------------------

        for component, count in (
            component_counter.items()
        ):

            percentage = round(
                (count / total_bugs) * 100,
                2
            )

            if percentage >= 30:

                systemic_patterns.append({

                    "type":
                        "Affected Component",

                    "pattern":
                        component,

                    "count":
                        count,

                    "percentage":
                        percentage
                })

        # ----------------------------------------------------
        # Root Cause Patterns
        # ----------------------------------------------------

        for root_cause, count in (
            root_cause_counter.items()
        ):

            percentage = round(
                (count / total_bugs) * 100,
                2
            )

            if percentage >= 30:

                systemic_patterns.append({

                    "type":
                        "Recurring Root Cause",

                    "pattern":
                        root_cause,

                    "count":
                        count,

                    "percentage":
                        percentage
                })

    # ========================================================
    # Final Dashboard Data
    # ========================================================

    return {

        # Total
        "total_bugs":
            total_bugs,

        # Severity
        "severity":
            dict(severity_counter),

        "severity_distribution":
            dict(severity_counter),

        # Components
        "components":
            dict(component_counter),

        "affected_components":
            dict(component_counter),

        # Root Causes
        "root_causes":
            dict(root_cause_counter),

        # Exceptions
        "exceptions":
            dict(exception_counter),

        # Trends
        "trends":
            dict(
                sorted(
                    date_counter.items()
                )
            ),

        "bug_trends":
            dict(
                sorted(
                    date_counter.items()
                )
            ),

        # Systemic Patterns
        "systemic_patterns":
            systemic_patterns
    }