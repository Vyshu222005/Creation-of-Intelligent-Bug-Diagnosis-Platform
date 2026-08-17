from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import re
import time

try:
    import numpy as np
except Exception:
    np = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import faiss
except Exception:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

try:
    from utils.triage_agent import triage_bug
except Exception:
    triage_bug = None

try:
    from utils.log_analysis import analyze_log
except Exception:
    analyze_log = None

try:
    from utils.root_cause_agent import root_cause_analysis as external_root_cause
except Exception:
    external_root_cause = None

try:
    from utils.remediation_agent import generate_remediation
except Exception:
    generate_remediation = None

# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "bug-diagnosis-platform-secret-key"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ANALYSIS_FOLDER = os.path.join(BASE_DIR, "analysis")
DATASET_FOLDER = os.path.join(BASE_DIR, "dataset")
KB_FOLDER = os.path.join(DATASET_FOLDER, "growth_knowledge_base")

BUG_REPORTS_FILE = os.path.join(BASE_DIR, "bug_reports.json")
VERIFIED_BUGS_FILE = os.path.join(KB_FOLDER, "verified_bugs.json")
VERIFIED_INDEX_FILE = os.path.join(KB_FOLDER, "verified_bugs.faiss")

MOZILLA_CSV = os.path.join(
    DATASET_FOLDER, "mozilla", "clean_mozilla.csv"
)
MOZILLA_INDEX = os.path.join(
    DATASET_FOLDER, "mozilla", "bug_index.faiss"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANALYSIS_FOLDER, exist_ok=True)
os.makedirs(KB_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def preserve_text(value):
    return str(value or "").strip()


def load_json_file(path, default):
    if not os.path.isfile(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        print(f"JSON read error [{path}]: {exc}")
        return default


def save_json_file(path, data):
    try:
        parent = os.path.dirname(path)

        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception as exc:
        print(f"JSON save error [{path}]: {exc}")
        return False


def get_analysis_path(bug_id):
    return os.path.join(
        ANALYSIS_FOLDER,
        f"bug_{bug_id}.json"
    )


def load_bug_reports():
    data = load_json_file(
        BUG_REPORTS_FILE,
        []
    )

    return data if isinstance(data, list) else []


def save_bug_reports(reports):
    return save_json_file(
        BUG_REPORTS_FILE,
        reports
    )


def load_verified_bugs():
    data = load_json_file(
        VERIFIED_BUGS_FILE,
        []
    )

    return data if isinstance(data, list) else []


def save_verified_bugs(bugs):
    return save_json_file(
        VERIFIED_BUGS_FILE,
        bugs
    )


def next_bug_id():
    ids = []

    for item in load_bug_reports():

        if not isinstance(item, dict):
            continue

        try:
            ids.append(
                int(
                    item.get("bug_id")
                    or item.get("id")
                )
            )
        except (TypeError, ValueError):
            pass

    return max(ids, default=0) + 1


# ============================================================
# COMPONENT DETECTION
# ============================================================

def detect_component(text):

    value = clean_text(text).lower()

    groups = {
        "Authentication": [
            "login",
            "signin",
            "sign in",
            "password",
            "credential",
            "authentication",
            "authorization",
            "jwt",
            "session"
        ],

        "Database": [
            "database",
            "mysql",
            "postgres",
            "postgresql",
            "mongodb",
            "sql",
            "query",
            "repository",
            "jdbc"
        ],

        "API": [
            "api",
            "endpoint",
            "http",
            "request",
            "response",
            "rest",
            "token",
            "service"
        ],

        "User Interface": [
            "html",
            "css",
            "button",
            "page",
            "screen",
            "frontend",
            "react",
            "ui",
            "layout"
        ],

        "File System": [
            "file",
            "upload",
            "download",
            "directory",
            "storage"
        ],

        "Network": [
            "network",
            "socket",
            "connection",
            "timeout",
            "internet"
        ]
    }

    for component, words in groups.items():

        if any(
            word in value
            for word in words
        ):
            return component

    return "General Software"


# ============================================================
# TRIAGE
# ============================================================

def fallback_triage(text):

    value = clean_text(text).lower()

    if any(
        x in value
        for x in [
            "nullpointerexception",
            "system crash",
            "application crash",
            "data loss",
            "security breach",
            "production down"
        ]
    ):
        severity = "Critical"
        priority = "P1"
        confidence = 92

    elif any(
        x in value
        for x in [
            "exception",
            "failed",
            "failure",
            "crash",
            "error",
            "timeout"
        ]
    ):
        severity = "High"
        priority = "P2"
        confidence = 88

    elif any(
        x in value
        for x in [
            "slow",
            "warning",
            "delay",
            "minor"
        ]
    ):
        severity = "Medium"
        priority = "P3"
        confidence = 80

    else:
        severity = "Low"
        priority = "P4"
        confidence = 72

    return {
        "severity": severity,
        "priority": priority,
        "component": detect_component(text),
        "confidence": confidence,
        "reasoning":
            "Severity and component were inferred from "
            "the submitted error information."
    }


def run_triage(text):

    if triage_bug is not None:

        try:
            result = triage_bug(text)

            if isinstance(result, dict):

                result.setdefault(
                    "severity",
                    "Medium"
                )

                result.setdefault(
                    "priority",
                    "P2"
                )

                result.setdefault(
                    "component",
                    detect_component(text)
                )

                result.setdefault(
                    "confidence",
                    80
                )

                result.setdefault(
                    "reasoning",
                    "AI triage completed."
                )

                return result

        except Exception as exc:
            print(
                "Triage agent error:",
                exc
            )

    return fallback_triage(text)


# ============================================================
# LOG ANALYSIS
# ============================================================

def fallback_log_analysis(text):

    value = preserve_text(text)

    issues = []

    patterns = [
        (
            "NullPointerException",
            r"NullPointerException"
        ),
        (
            "AttributeError",
            r"AttributeError"
        ),
        (
            "TypeError",
            r"TypeError"
        ),
        (
            "ValueError",
            r"ValueError"
        ),
        (
            "KeyError",
            r"KeyError"
        ),
        (
            "IndexError",
            r"IndexError"
        ),
        (
            "SQLException",
            r"(?:SQLException|SQLSyntaxErrorException)"
        ),
        (
            "HTTPError",
            r"HTTP(?:Error|Exception)"
        ),
        (
            "TimeoutError",
            r"TimeoutError"
        )
    ]

    exception = "UnknownException"

    for name, pattern in patterns:

        if re.search(
            pattern,
            value,
            re.IGNORECASE
        ):
            exception = name
            break

    lines = value.splitlines()

    failure_point = ""
    line_number = ""
    code_path = ""

    for line in lines:

        if re.search(
            r"\bat\s+[\w.$]+\([^)]*:\d+\)",
            line
        ):
            failure_point = line.strip()

            match = re.search(
                r":(\d+)\)",
                line
            )

            line_number = (
                match.group(1)
                if match
                else ""
            )

            code_path = line.strip()
            break

    if value:

        issues.append({
            "exception_type": exception,
            "failure_point":
                failure_point
                or "Not identified",

            "line_number":
                line_number
                or "-",

            "code_path":
                code_path
                or "-",

            "error_message":
                clean_text(
                    lines[0]
                    if lines
                    else value
                )[:500],

            "root_cause":
                "The failure pattern requires review "
                "of the submitted trace.",

            "severity":
                "High"
                if exception != "UnknownException"
                else "Medium",

            "suggested_fix":
                "Inspect the failure point and "
                "validate the related input/object."
        })

    return {
        "issues": issues
    }


def run_log_analysis(text):

    if analyze_log is not None:

        try:
            result = analyze_log(text)

            if isinstance(result, dict):
                return result

        except Exception as exc:
            print(
                "Log analysis agent error:",
                exc
            )

    return fallback_log_analysis(text)


# ============================================================
# ROOT CAUSE
# ============================================================

def fallback_root_cause(
    bug_text,
    log_data,
    similar_bugs
):

    issues = (
        log_data.get("issues", [])
        if isinstance(log_data, dict)
        else []
    )

    exception = ""
    failure_point = ""

    if issues and isinstance(
        issues[0],
        dict
    ):

        exception = clean_text(
            issues[0].get(
                "exception_type",
                ""
            )
        )

        failure_point = clean_text(
            issues[0].get(
                "failure_point",
                ""
            )
        )

    component = detect_component(
        bug_text
    )

    if exception == "NullPointerException":

        cause = (
            "A required object or user record "
            "is null before it is accessed."
        )

    elif component == "Database":

        cause = (
            "The application likely received "
            "an invalid or missing database result."
        )

    elif component == "Authentication":

        cause = (
            "The authentication flow is not safely "
            "handling an invalid or missing user state."
        )

    elif exception:

        cause = (
            f"The application is failing with "
            f"{exception}, with the failure occurring "
            f"near {failure_point or 'the reported execution path'}."
        )

    else:

        cause = (
            "The submitted defect indicates an application "
            "logic or runtime failure that needs investigation."
        )

    # Dynamic confidence based on available evidence
    historical_similarity = 0.0

    if isinstance(similar_bugs, list):
        similarities = []
        for bug in similar_bugs[:5]:
            if not isinstance(bug, dict):
                continue
            try:
                value = float(bug.get("similarity", 0) or 0)
                if 0 <= value <= 1:
                    value *= 100
                similarities.append(value)
            except (TypeError, ValueError):
                continue
        if similarities:
            historical_similarity = max(similarities)

    evidence_count = sum([
        bool(exception),
        bool(failure_point),
        historical_similarity >= 40
    ])

    if evidence_count >= 3:
        confidence = 88
    elif evidence_count == 2:
        confidence = 78
    elif evidence_count == 1:
        confidence = 62
    else:
        confidence = 45

    confidence += min(7, historical_similarity * 0.07)
    confidence = int(max(40, min(95, round(confidence))))

    return {
        "root_cause": cause,
        "confidence": confidence,
        "evidence": [
            f"Detected component: {component}.",
            f"Log analysis identified {exception or 'no specific exception'}.",
            f"Historical bug similarity was considered ({historical_similarity:.1f}%)."
        ]
    }


def calculate_root_cause_confidence(
    log_data,
    similar_bugs,
    root_cause_text=""
):
    """
    Calculate a dynamic confidence score for Root Cause Analysis.

    The score is based on the evidence actually available:
    - exception type
    - failure point
    - error message
    - code path
    - historical FAISS similarity
    - presence of a concrete root-cause explanation

    This prevents a fixed value such as 85% or 91% from being
    displayed for every bug.
    """

    issues = (
        log_data.get("issues", [])
        if isinstance(log_data, dict)
        else []
    )

    issue = (
        issues[0]
        if issues
        and isinstance(issues[0], dict)
        else {}
    )

    exception = clean_text(
        issue.get("exception_type", "")
    )

    failure_point = clean_text(
        issue.get("failure_point", "")
    )

    error_message = clean_text(
        issue.get("error_message", "")
    )

    code_path = clean_text(
        issue.get("code_path", "")
    )

    # "UnknownException" and placeholder values are not strong evidence.
    if exception.lower() in {
        "",
        "unknown",
        "unknownexception",
        "not identified",
        "-"
    }:
        exception = ""

    if failure_point.lower() in {
        "",
        "not identified",
        "-"
    }:
        failure_point = ""

    if error_message.lower() in {
        "",
        "not identified",
        "-"
    }:
        error_message = ""

    if code_path.lower() in {
        "",
        "not identified",
        "-"
    }:
        code_path = ""

    # Find the strongest historical similarity.
    historical_similarity = 0.0

    if isinstance(similar_bugs, list):

        similarities = []

        for bug in similar_bugs[:5]:

            if not isinstance(bug, dict):
                continue

            try:
                value = float(
                    bug.get(
                        "similarity",
                        0
                    )
                    or 0
                )

                if 0 <= value <= 1:
                    value *= 100

                similarities.append(
                    max(
                        0,
                        min(
                            100,
                            value
                        )
                    )
                )

            except (
                TypeError,
                ValueError
            ):
                continue

        if similarities:
            historical_similarity = max(
                similarities
            )

    # Evidence-based score.
    score = 40

    if exception:
        score += 12

    if failure_point:
        score += 10

    if error_message:
        score += 8

    if code_path:
        score += 8

    if clean_text(root_cause_text):
        score += 5

    # Historical similarity contributes gradually.
    # 0% similarity adds 0, 100% adds at most 17.
    score += (
        historical_similarity * 0.17
    )

    confidence = int(
        max(
            40,
            min(
                95,
                round(score)
            )
        )
    )

    return {
        "confidence": confidence,
        "historical_similarity": round(
            historical_similarity,
            2
        ),
        "evidence_count": sum([
            bool(exception),
            bool(failure_point),
            bool(error_message),
            bool(code_path)
        ])
    }


def run_root_cause(
    text,
    log_data,
    similar_bugs
):

    result = None

    if external_root_cause is not None:

        try:

            result = external_root_cause(
                text,
                log_data,
                similar_bugs
            )

        except TypeError:

            try:

                result = external_root_cause(
                    text,
                    similar_bugs,
                    log_data
                )

            except Exception as exc:

                print(
                    "Root cause agent error:",
                    exc
                )

        except Exception as exc:

            print(
                "Root cause agent error:",
                exc
            )

    # If the external Root Cause Agent produced a result,
    # keep its diagnosis/evidence but calculate the displayed
    # confidence from the actual evidence available.
    if isinstance(result, dict):

        root_text = clean_text(
            result.get(
                "root_cause",
                ""
            )
        )

        confidence_data = (
            calculate_root_cause_confidence(
                log_data,
                similar_bugs,
                root_text
            )
        )

        result["confidence"] = (
            confidence_data["confidence"]
        )

        result["historical_similarity"] = (
            confidence_data[
                "historical_similarity"
            ]
        )

        result["evidence_count"] = (
            confidence_data[
                "evidence_count"
            ]
        )

        result["confidence_reasoning"] = (
            "Confidence was calculated from the available "
            "exception, failure point, error message, code "
            "path, root-cause explanation, and historical "
            "semantic similarity evidence."
        )

        return result

    # Safe local fallback.
    result = fallback_root_cause(
        text,
        log_data,
        similar_bugs
    )

    confidence_data = (
        calculate_root_cause_confidence(
            log_data,
            similar_bugs,
            result.get(
                "root_cause",
                ""
            )
        )
    )

    result["confidence"] = (
        confidence_data["confidence"]
    )

    result["historical_similarity"] = (
        confidence_data[
            "historical_similarity"
        ]
    )

    result["evidence_count"] = (
        confidence_data[
            "evidence_count"
        ]
    )

    result["confidence_reasoning"] = (
        "Confidence was calculated from the available "
        "diagnostic evidence."
    )

    return result


# ============================================================
# REMEDIATION
# ============================================================

def fallback_remediation(
    text,
    triage,
    log_data,
    root_cause
):

    component = triage.get(
        "component",
        detect_component(text)
    )

    cause = clean_text(
        root_cause.get(
            "root_cause",
            ""
        )
    )

    if component == "Authentication":

        steps = [
            "Validate the user input and authentication state.",
            "Handle missing or invalid users safely.",
            "Add clear authentication error handling.",
            "Run regression tests for valid and invalid login attempts."
        ]

    elif component == "Database":

        steps = [
            "Verify database connectivity and credentials.",
            "Validate query results before using returned objects.",
            "Handle missing records safely.",
            "Run database integration tests."
        ]

    else:

        steps = [
            "Reproduce the defect consistently.",
            "Review the identified failure point.",
            "Apply the fix for the probable root cause.",
            "Run functional and regression tests."
        ]

    return {
        "summary":
            cause
            or
            "Apply the recommended correction "
            "and validate the affected flow.",

        "recommended_steps": steps,
        "steps": steps,

        "testing": [
            "Functional testing.",
            "Regression testing.",
            "Integration testing."
        ],

        "prevention": [
            "Improve input validation.",
            "Add useful error logging.",
            "Add automated regression coverage."
        ]
    }

def run_remediation(
    text,
    triage,
    log_data,
    root_cause
):
    """
    Run the remediation agent and clean its output
    before sending it to result.html.
    """

    result = None

    # ---------------------------------------------------------
    # RUN REMEDIATION AGENT
    # ---------------------------------------------------------

    if generate_remediation is not None:

        try:

            result = generate_remediation(
                text,
                triage,
                log_data,
                root_cause
            )

        except Exception as exc:

            print(
                "Remediation agent error:",
                exc
            )

    # ---------------------------------------------------------
    # SAFE FALLBACK
    # ---------------------------------------------------------

    if not isinstance(result, dict):

        result = {
            "summary":
                "Apply the identified corrective action "
                "and verify the affected functionality.",

            "recommended_steps": [],

            "steps": [],

            "testing": [
                "Functional testing.",
                "Regression testing.",
                "Integration testing."
            ],

            "prevention": [
                "Improve input validation.",
                "Add appropriate exception handling.",
                "Add automated regression tests."
            ]
        }

    # ---------------------------------------------------------
    # GET STEPS
    # ---------------------------------------------------------

    steps = result.get(
        "recommended_steps",
        result.get(
            "steps",
            []
        )
    )

    if not isinstance(steps, list):

        steps = [steps]

    # ---------------------------------------------------------
    # CLEAN + REMOVE DUPLICATES
    # ---------------------------------------------------------

    cleaned_steps = []
    seen = set()

    for step in steps:

        if step is None:
            continue

        step = str(step).strip()

        if not step:
            continue

        # Remove excessive whitespace
        step = " ".join(
            step.split()
        )

        # -----------------------------------------------------
        # Ignore extremely long historical paragraphs
        # -----------------------------------------------------

        if len(step) > 500:

            print(
                "Skipped oversized remediation step."
            )

            continue

        # -----------------------------------------------------
        # Normalize duplicate comparison
        # -----------------------------------------------------

        key = step.lower()

        if key in seen:
            continue

        seen.add(key)

        cleaned_steps.append(
            step
        )

        # Maximum 6 recommendations
        if len(cleaned_steps) >= 6:
            break

    # ---------------------------------------------------------
    # IF NOTHING VALID REMAINS
    # ---------------------------------------------------------

    if not cleaned_steps:

        component = str(
            triage.get(
                "component",
                "Software"
            )
        )

        if "authentication" in component.lower():

            cleaned_steps = [
                "Validate username and password before authentication.",
                "Handle invalid or missing user credentials safely.",
                "Add null checks and exception handling.",
                "Add regression tests for invalid login attempts."
            ]

        else:

            cleaned_steps = [
                "Validate all inputs before processing.",
                "Handle exceptions around the failing operation.",
                "Apply the corrective code change.",
                "Run functional and regression tests."
            ]

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    result["recommended_steps"] = cleaned_steps

    # Keep compatibility with result.html
    result["steps"] = cleaned_steps

    # ---------------------------------------------------------
    # CLEAN TESTING
    # ---------------------------------------------------------

    testing = result.get(
        "testing",
        []
    )

    if not isinstance(testing, list):
        testing = [testing]

    testing_clean = []
    testing_seen = set()

    for item in testing:

        if item is None:
            continue

        item = " ".join(
            str(item).strip().split()
        )

        if not item:
            continue

        key = item.lower()

        if key in testing_seen:
            continue

        testing_seen.add(key)

        testing_clean.append(item)

    result["testing"] = testing_clean[:4]

    # ---------------------------------------------------------
    # CLEAN PREVENTION
    # ---------------------------------------------------------

    prevention = result.get(
        "prevention",
        []
    )

    if not isinstance(prevention, list):
        prevention = [prevention]

    prevention_clean = []
    prevention_seen = set()

    for item in prevention:

        if item is None:
            continue

        item = " ".join(
            str(item).strip().split()
        )

        if not item:
            continue

        key = item.lower()

        if key in prevention_seen:
            continue

        prevention_seen.add(key)

        prevention_clean.append(item)

    result["prevention"] = prevention_clean[:4]

    print(
        "Final remediation steps:",
        result["recommended_steps"]
    )

    return result


# ============================================================
# SMART FIX ADVISOR
# ============================================================

def generate_fix_advisor(
    text,
    triage,
    root_cause,
    log_data
):

    component = triage.get(
        "component",
        detect_component(text)
    )

    priority = triage.get(
        "priority",
        "P2"
    )

    severity = triage.get(
        "severity",
        "Medium"
    )

    cause = clean_text(
        root_cause.get(
            "root_cause",
            ""
        )
    )

    if component == "Authentication":

        category = "Authentication"

        fixes = [
            "Validate username and password before authentication.",
            "Handle invalid or missing users safely.",
            "Review session and authorization handling.",
            "Add regression tests for invalid login attempts."
        ]

    elif component == "Database":

        category = "Database"

        fixes = [
            "Verify database connectivity and credentials.",
            "Validate query results before accessing them.",
            "Handle missing database records safely.",
            "Run database integration tests."
        ]

    elif component == "API":

        category = "API"

        fixes = [
            "Validate the request payload.",
            "Verify endpoint and authentication configuration.",
            "Handle timeout and error responses.",
            "Add API integration tests."
        ]

    else:

        category = "General Software Bug"

        fixes = [
            "Reproduce the issue consistently.",
            "Review application logs and the failure point.",
            "Apply the correction for the probable root cause.",
            "Perform regression testing."
        ]

    return {
        "category": category,
        "priority": priority,
        "severity": severity,
        "root_cause":
            cause
            or
            "Further investigation is required.",

        "impact":
            "The affected feature may produce "
            "unexpected application behavior.",

        "recommended_fix": fixes,

        "testing": [
            "Functional testing.",
            "Regression testing.",
            "Integration testing."
        ],

        "prevention": [
            "Improve validation.",
            "Improve logging.",
            "Automate regression tests."
        ]
    }


# ============================================================
# HISTORICAL DATA
# ============================================================

embedding_model = None
mozilla_data = None
mozilla_index = None


def load_ml_resources():

    global embedding_model
    global mozilla_data
    global mozilla_index

    if (
        SentenceTransformer is not None
        and embedding_model is None
    ):

        try:
            embedding_model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

        except Exception as exc:
            print(
                "Sentence Transformer unavailable:",
                exc
            )

    if (
        pd is not None
        and mozilla_data is None
        and os.path.isfile(MOZILLA_CSV)
    ):

        try:
            mozilla_data = pd.read_csv(
                MOZILLA_CSV
            )

        except Exception as exc:
            print(
                "Mozilla dataset unavailable:",
                exc
            )

    if (
        faiss is not None
        and mozilla_index is None
        and os.path.isfile(MOZILLA_INDEX)
    ):

        try:
            mozilla_index = faiss.read_index(
                MOZILLA_INDEX
            )

        except Exception as exc:
            print(
                "Mozilla FAISS index unavailable:",
                exc
            )


load_ml_resources()


def prepare_historical_bugs(
    bugs,
    limit=3
):

    if not isinstance(
        bugs,
        list
    ):
        return []

    results = []
    seen = set()

    for bug in bugs:

        if not isinstance(
            bug,
            dict
        ):
            continue

        bug_id = (
            bug.get("bug_id")
            or bug.get("id")
            or ""
        )

        title = clean_text(
            bug.get(
                "bug_title",
                bug.get(
                    "title",
                    ""
                )
            )
        )

        description = clean_text(
            bug.get(
                "bug_report",
                bug.get(
                    "description",
                    ""
                )
            )
        ) or title

        if not description:
            continue

        key = (
            title
            + " "
            + description
        ).lower()

        if key in seen:
            continue

        seen.add(key)

        try:

            similarity = float(
                bug.get(
                    "similarity",
                    bug.get(
                        "score",
                        0
                    )
                )
                or 0
            )

            if 0 <= similarity <= 1:
                similarity *= 100

        except Exception:
            similarity = 0

        results.append({
            "bug_id":
                bug_id
                or len(results) + 1,

            "id":
                bug_id
                or len(results) + 1,

            "title":
                title
                or "Historical Bug",

            "description":
                description[:500],

            "severity":
                str(
                    bug.get(
                        "severity",
                        "Unknown"
                    )
                ),

            "component":
                str(
                    bug.get(
                        "component",
                        "Unknown"
                    )
                ),

            "root_cause":
                clean_text(
                    bug.get(
                        "root_cause",
                        ""
                    )
                ),

            "resolution":
                clean_text(
                    bug.get(
                        "resolution",
                        ""
                    )
                ),

            "similarity":
                round(
                    max(
                        0,
                        min(
                            100,
                            similarity
                        )
                    ),
                    2
                )
        })

        if len(results) >= limit:
            break

    for rank, item in enumerate(
        results,
        start=1
    ):
        item["rank"] = rank

    return results


def search_historical_bugs(
    query,
    top_k=5
):

    load_ml_resources()

    if (
        embedding_model is not None
        and mozilla_index is not None
        and mozilla_data is not None
    ):

        try:

            vector = embedding_model.encode(
                [query],
                convert_to_numpy=True
            ).astype("float32")

            distances, indices = (
                mozilla_index.search(
                    vector,
                    top_k
                )
            )

            results = []

            for rank, idx in enumerate(
                indices[0]
            ):

                if (
                    idx < 0
                    or idx >= len(mozilla_data)
                ):
                    continue

                distance = float(
                    distances[0][rank]
                )

                similarity = (
                    1.0
                    /
                    (1.0 + max(distance, 0.0))
                ) * 100

                row = mozilla_data.iloc[
                    int(idx)
                ]

                description = clean_text(
                    row.get(
                        "Description",
                        row.get(
                            "description",
                            ""
                        )
                    )
                )

                results.append({
                    "bug_id":
                        row.get(
                            "Bug ID",
                            row.get(
                                "id",
                                rank + 1
                            )
                        ),

                    "title":
                        clean_text(
                            row.get(
                                "Summary",
                                row.get(
                                    "Title",
                                    "Historical Bug"
                                )
                            )
                        ),

                    "description":
                        description[:500],

                    "severity":
                        str(
                            row.get(
                                "Severity",
                                "Unknown"
                            )
                        ),

                    "component":
                        clean_text(
                            row.get(
                                "Component",
                                "Unknown"
                            )
                        ),

                    "similarity":
                        round(
                            similarity,
                            2
                        )
                })

            return prepare_historical_bugs(
                results,
                limit=top_k
            )

        except Exception as exc:
            print(
                "Historical search error:",
                exc
            )

    return prepare_historical_bugs(
        load_verified_bugs(),
        limit=top_k
    )


def detect_duplicates(
    similar_bugs
):

    if not similar_bugs:
        return []

    best = max(
        similar_bugs,
        key=lambda item:
            float(
                item.get(
                    "similarity",
                    0
                )
                or 0
            )
    )

    similarity = float(
        best.get(
            "similarity",
            0
        )
        or 0
    )

    if similarity < 80:
        return []

    return [{
        "bug_id":
            best.get(
                "bug_id",
                "Unknown"
            ),

        "title":
            best.get(
                "title",
                "Possible Duplicate Bug"
            ),

        "bug":
            best.get(
                "description",
                ""
            ),

        "similarity":
            round(
                similarity,
                2
            ),

        "resolution":
            best.get(
                "resolution",
                "Review the historical resolution."
            )
    }]


# ============================================================
# KNOWLEDGE BASE
# ============================================================

def rebuild_knowledge_base_index():

    bugs = load_verified_bugs()

    if (
        not bugs
        or embedding_model is None
        or faiss is None
        or np is None
    ):
        return False

    texts = []

    for bug in bugs:

        texts.append(
            clean_text(
                bug.get(
                    "bug_title",
                    ""
                )
            )
            + " "
            + clean_text(
                bug.get(
                    "bug_report",
                    ""
                )
            )
        )

    try:

        vectors = embedding_model.encode(
            texts,
            convert_to_numpy=True
        ).astype("float32")

        index = faiss.IndexFlatL2(
            vectors.shape[1]
        )

        index.add(vectors)

        faiss.write_index(
            index,
            VERIFIED_INDEX_FILE
        )

        return True

    except Exception as exc:
        print(
            "Knowledge base rebuild error:",
            exc
        )
        return False


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# ANALYZE BUG
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    start_time = time.time()

    bug_title = preserve_text(
        request.form.get(
            "bug_title"
        )
    )

    # The page now has NO Bug Description box.
    # This field contains the manually pasted Stack Trace / Error Log.
    bug_report = preserve_text(
        request.form.get(
            "bug_report"
        )
        or
        request.form.get(
            "stack_trace"
        )
    )

    category = clean_text(
        request.form.get(
            "category"
        )
        or
        "General Software Bug"
    )

    if not bug_title:

        flash(
            "Please enter a bug title.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    if not bug_report:

        flash(
            "Please paste the Stack Trace / Error Log.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    reports = load_bug_reports()

    bug_id = next_bug_id()

    uploaded_file = request.files.get(
        "log_file"
    )

    filename = ""
    log_text = ""

    if (
        uploaded_file
        and uploaded_file.filename
    ):

        filename = secure_filename(
            uploaded_file.filename
        )

        if filename:

            path = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            try:

                uploaded_file.save(
                    path
                )

                with open(
                    path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as file:

                    log_text = file.read()

            except Exception as exc:

                print(
                    "Uploaded file error:",
                    exc
                )

    analysis_input = bug_report

    if log_text:

        analysis_input += (
            "\n\nUploaded Log File:\n"
            + log_text
        )

    # --------------------------------------------------------
    # Agent 1 - Triage
    # --------------------------------------------------------

    triage_result = run_triage(
        analysis_input
    )

    # --------------------------------------------------------
    # Agent 2 - Log Analysis
    # --------------------------------------------------------

    log_result = run_log_analysis(
        log_text
        or
        analysis_input
    )

    # Remove repeated log issues.
    if isinstance(
        log_result,
        dict
    ):

        issues = log_result.get(
            "issues",
            []
        )

        if isinstance(
            issues,
            list
        ):

            unique_issues = []
            seen_issues = set()

            for issue in issues:

                if not isinstance(
                    issue,
                    dict
                ):
                    continue

                issue_key = (
                    clean_text(
                        issue.get(
                            "exception_type",
                            ""
                        )
                    ).lower(),

                    clean_text(
                        issue.get(
                            "failure_point",
                            ""
                        )
                    ).lower(),

                    clean_text(
                        issue.get(
                            "error_message",
                            ""
                        )
                    ).lower()
                )

                if issue_key in seen_issues:
                    continue

                seen_issues.add(
                    issue_key
                )

                unique_issues.append(
                    issue
                )

            log_result["issues"] = (
                unique_issues[:5]
            )

    # --------------------------------------------------------
    # Historical Similarity
    # --------------------------------------------------------

    similar_bugs = search_historical_bugs(
        bug_title
        + "\n"
        + analysis_input,
        top_k=5
    )

    # --------------------------------------------------------
    # Agent 3 - Root Cause
    # --------------------------------------------------------

    root_cause_result = run_root_cause(
        analysis_input,
        log_result,
        similar_bugs
    )

    # --------------------------------------------------------
    # Agent 4 - Duplicate Detection
    # --------------------------------------------------------

    duplicate_result = detect_duplicates(
        similar_bugs
    )

    # --------------------------------------------------------
    # Agent 5 - Remediation
    # --------------------------------------------------------

    remediation_result = run_remediation(
        analysis_input,
        triage_result,
        log_result,
        root_cause_result
    )

    # --------------------------------------------------------
    # Smart Fix Advisor
    # --------------------------------------------------------

    fix_advisor = generate_fix_advisor(
        analysis_input,
        triage_result,
        root_cause_result,
        log_result
    )

    processing_time = round(
        time.time() - start_time,
        2
    )

    submission_date = datetime.now().strftime(
        "%d-%m-%Y %I:%M %p"
    )

    # --------------------------------------------------------
    # Combined Analysis
    # --------------------------------------------------------

    analysis = {
        "bug_id": str(bug_id),

        "bug_title": bug_title,

        "bug_report": bug_report,

        "category": category,

        "uploaded_file":
            filename
            or
            "None",

        "submission_date":
            submission_date,

        "processing_time":
            processing_time,

        "triage":
            triage_result,

        "triage_analysis":
            triage_result,

        "log_analysis":
            log_result,

        "similar_bugs":
            similar_bugs[:5],

        "similar_historical_bugs":
            similar_bugs[:3],

        "historical_bugs":
            similar_bugs[:3],

        "duplicate_detection":
            duplicate_result,

        "duplicates":
            duplicate_result,

        "root_cause_analysis":
            root_cause_result,

        "root_cause":
            root_cause_result,

        "remediation":
            remediation_result,

        "fix_advisor":
            fix_advisor,

        "ai_smart_fix":
            fix_advisor,

        "resolved":
            False
    }

    # Save JSON.
    save_json_file(
        get_analysis_path(bug_id),
        analysis
    )

    # Save report for analytics.
    reports.append({
        "bug_id":
            str(bug_id),

        "bug_title":
            bug_title,

        "bug_report":
            bug_report,

        "category":
            category,

        "severity":
            triage_result.get(
                "severity",
                "Unknown"
            ),

        "priority":
            triage_result.get(
                "priority",
                "P2"
            ),

        "component":
            triage_result.get(
                "component",
                detect_component(
                    analysis_input
                )
            ),

        "confidence":
            triage_result.get(
                "confidence",
                0
            ),

        "created_at":
            datetime.now().isoformat(),

        "resolved":
            False
    })

    save_bug_reports(
        reports
    )

    return render_template(
        "result.html",

        analysis=analysis,

        bug_id=str(
            bug_id
        ),

        bug_title=bug_title,

        bug_report=bug_report,

        triage=triage_result,

        triage_analysis=triage_result,

        log_analysis=log_result,

        similar_bugs=similar_bugs,

        historical_bugs=similar_bugs[:3],

        duplicate_detection=
            duplicate_result,

        duplicates=
            duplicate_result,

        root_cause=
            root_cause_result,

        root_cause_analysis=
            root_cause_result,

        remediation=
            remediation_result,

        fix_advisor=
            fix_advisor,

        processing_time=
            processing_time,

        uploaded_file=
            filename
            or
            "None"
    )


# ============================================================
# RESULT PAGE
# ============================================================

@app.route(
    "/result/<bug_id>",
    methods=["GET"]
)
def result_page(
    bug_id
):

    analysis = load_json_file(
        get_analysis_path(bug_id),
        None
    )

    if not isinstance(
        analysis,
        dict
    ):
        return (
            "Analysis report not found.",
            404
        )

    similar = prepare_historical_bugs(
        analysis.get(
            "similar_bugs",
            []
        ),
        limit=3
    )

    duplicates = analysis.get(
        "duplicate_detection",
        []
    )

    if not isinstance(
        duplicates,
        list
    ):
        duplicates = []

    triage = analysis.get(
        "triage",
        {}
    )

    log_analysis = analysis.get(
        "log_analysis",
        {}
    )

    root_cause = analysis.get(
        "root_cause_analysis",
        {}
    )

    remediation = analysis.get(
        "remediation",
        {}
    )

    fix_advisor = analysis.get(
        "fix_advisor",
        {}
    )

    return render_template(
        "result.html",

        analysis=analysis,

        bug_id=str(
            bug_id
        ),

        bug_title=
            analysis.get(
                "bug_title",
                ""
            ),

        bug_report=
            analysis.get(
                "bug_report",
                ""
            ),

        triage=triage,

        triage_analysis=
            triage,

        log_analysis=
            log_analysis,

        similar_bugs=
            similar,

        historical_bugs=
            similar,

        duplicate_detection=
            duplicates[:1],

        duplicates=
            duplicates[:1],

        root_cause=
            root_cause,

        root_cause_analysis=
            root_cause,

        remediation=
            remediation,

        fix_advisor=
            fix_advisor,

        processing_time=
            analysis.get(
                "processing_time",
                0
            ),

        uploaded_file=
            analysis.get(
                "uploaded_file",
                "None"
            )
    )


# ============================================================
# DOWNLOAD REPORT
# ============================================================

@app.route(
    "/download-report/<int:bug_id>"
)
def download_report(
    bug_id
):

    path = get_analysis_path(
        bug_id
    )

    if not os.path.isfile(path):

        return jsonify({
            "success":
                False,

            "message":
                "Analysis report not found."
        }), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=
            f"bug_{bug_id}_analysis.json",
        mimetype=
            "application/json"
    )


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/analytics")
def analytics():

    reports = load_bug_reports()

    # ============================================================
    # ANALYTICS COUNTERS
    # ============================================================

    severity = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0
    }

    priority = {
        "P1": 0,
        "P2": 0,
        "P3": 0,
        "P4": 0
    }

    components = {}
    exceptions = {}
    root_causes = {}

    resolved = 0
    unresolved = 0

    confidence_values = []

    total_matches = 0
    bugs_with_matches = 0

    # ============================================================
    # ROOT CAUSE NORMALIZATION
    # ============================================================

    def normalize_root_cause(text):

        text = clean_text(text)

        if not text:
            return "Unknown Root Cause"

        value = text.lower()

        # Null / None related problems
        if any(x in value for x in [
            "nullpointerexception",
            "null pointer",
            "is null",
            "was null",
            "null before",
            "none value",
            "null value"
        ]):
            if any(x in value for x in [
                "username",
                "password",
                "input",
                "parameter",
                "validation",
                "authentication"
            ]):
                return "Null Handling / Input Validation"

            return "Null Reference Handling"

        # Authentication
        if any(x in value for x in [
            "authentication",
            "login",
            "username",
            "password",
            "credential",
            "authorization"
        ]):
            return "Authentication / Login Validation"

        # Input validation
        if any(x in value for x in [
            "input validation",
            "validate input",
            "invalid input",
            "missing input",
            "user input",
            "parameter validation"
        ]):
            return "Input Validation"

        # Exception handling
        if any(x in value for x in [
            "exception handling",
            "unhandled exception",
            "error handling",
            "catch exception"
        ]):
            return "Exception Handling"

        # Database
        if any(x in value for x in [
            "database",
            "sql",
            "query",
            "connection",
            "mysql",
            "postgres",
            "mongodb"
        ]):
            return "Database / Query Handling"

        # API
        if any(x in value for x in [
            "api",
            "http request",
            "request handling",
            "endpoint",
            "rest"
        ]):
            return "API / Request Handling"

        # File / resource
        if any(x in value for x in [
            "file",
            "filesystem",
            "resource",
            "path not found"
        ]):
            return "File / Resource Handling"

        # Configuration
        if any(x in value for x in [
            "configuration",
            "config",
            "environment variable",
            "settings"
        ]):
            return "Configuration Issue"

        # Concurrency
        if any(x in value for x in [
            "thread",
            "concurrency",
            "race condition",
            "deadlock"
        ]):
            return "Concurrency / Threading"

        # UI
        if any(x in value for x in [
            "user interface",
            "ui",
            "frontend",
            "display",
            "rendering"
        ]):
            return "User Interface"

        # Security
        if any(x in value for x in [
            "security",
            "vulnerability",
            "injection",
            "permission",
            "access control"
        ]):
            return "Security"

        # If nothing matches, keep a short meaningful version
        if len(text) > 80:
            return text[:80] + "..."

        return text

    # ============================================================
    # EXCEPTION NORMALIZATION
    # ============================================================

    def normalize_exception(text):

        text = clean_text(text)

        if not text:
            return "UnknownException"

        value = text.lower()

        if "nullpointerexception" in value:
            return "NullPointerException"

        if "indexoutofbound" in value:
            return "IndexOutOfBoundsException"

        if "arrayindexoutofbound" in value:
            return "ArrayIndexOutOfBoundsException"

        if "keyerror" in value:
            return "KeyError"

        if "typeerror" in value:
            return "TypeError"

        if "valueerror" in value:
            return "ValueError"

        if "attributeerror" in value:
            return "AttributeError"

        if "filenotfound" in value:
            return "FileNotFoundError"

        if "timeout" in value:
            return "TimeoutException"

        if "permission" in value:
            return "PermissionError"

        return text

    # ============================================================
    # PROCESS REPORTS
    # ============================================================

    for report in reports:

        if not isinstance(report, dict):
            continue

        # --------------------------------------------------------
        # RESOLUTION STATUS
        # --------------------------------------------------------

        if report.get("resolved"):
            resolved += 1
        else:
            unresolved += 1

        # --------------------------------------------------------
        # SEVERITY
        # --------------------------------------------------------

        sev = clean_text(
            report.get(
                "severity",
                "Unknown"
            )
        )

        if sev in severity:
            severity[sev] += 1

        # --------------------------------------------------------
        # PRIORITY
        # --------------------------------------------------------

        pri = clean_text(
            report.get(
                "priority",
                "Unknown"
            )
        )

        if pri in priority:
            priority[pri] += 1

        # --------------------------------------------------------
        # COMPONENT
        # --------------------------------------------------------

        component = clean_text(
            report.get(
                "component",
                "Unknown"
            )
        ) or "Unknown"

        # Normalize authentication components
        component_lower = component.lower()

        if any(x in component_lower for x in [
            "login",
            "authentication",
            "auth"
        ]):
            component = "Authentication"

        elif any(x in component_lower for x in [
            "database",
            "sql",
            "db"
        ]):
            component = "Database"

        elif any(x in component_lower for x in [
            "api",
            "endpoint",
            "rest"
        ]):
            component = "API"

        elif any(x in component_lower for x in [
            "ui",
            "interface",
            "frontend"
        ]):
            component = "User Interface"

        components[component] = (
            components.get(component, 0) + 1
        )

        # --------------------------------------------------------
        # CONFIDENCE
        # --------------------------------------------------------

        try:

            confidence = float(
                report.get(
                    "confidence",
                    0
                )
            )

            if confidence <= 1:
                confidence *= 100

            confidence_values.append(
                confidence
            )

        except Exception:
            pass

        # --------------------------------------------------------
        # LOAD ANALYSIS JSON
        # --------------------------------------------------------

        bug_id = report.get("bug_id")

        saved = load_json_file(
            get_analysis_path(bug_id),
            {}
        )

        if not isinstance(saved, dict):
            saved = {}

        # ========================================================
        # HISTORICAL MATCHES
        # ========================================================

        matches = saved.get(
            "similar_bugs",
            []
        )

        if (
            isinstance(matches, list)
            and matches
        ):

            bugs_with_matches += 1

            # Keep the same UI behaviour
            total_matches += min(
                len(matches),
                3
            )

        # ========================================================
        # LOG / EXCEPTION ANALYSIS
        # ========================================================

        log_data = saved.get(
            "log_analysis",
            {}
        )

        if isinstance(log_data, dict):

            issues = log_data.get(
                "issues",
                []
            )

            if isinstance(issues, list):

                for issue in issues:

                    if not isinstance(
                        issue,
                        dict
                    ):
                        continue

                    exc = normalize_exception(
                        issue.get(
                            "exception_type",
                            ""
                        )
                    )

                    if exc:

                        exceptions[exc] = (
                            exceptions.get(
                                exc,
                                0
                            ) + 1
                        )

        # ========================================================
        # ROOT CAUSE ANALYSIS
        # ========================================================

        root = saved.get(
            "root_cause_analysis",
            {}
        )

        if isinstance(root, dict):

            text = clean_text(
                root.get(
                    "root_cause",
                    ""
                )
            )

            if text:

                normalized = (
                    normalize_root_cause(
                        text
                    )
                )

                root_causes[
                    normalized
                ] = (
                    root_causes.get(
                        normalized,
                        0
                    ) + 1
                )

    # ============================================================
    # CALCULATIONS
    # ============================================================

    total = len(reports)

    # Average confidence
    if confidence_values:

        average_confidence = round(
            sum(confidence_values)
            / len(confidence_values),
            1
        )

    else:

        average_confidence = 0

    # Average historical matches
    if total:

        average_matches = round(
            total_matches / total,
            1
        )

    else:

        average_matches = 0

    # ============================================================
    # SORT ROOT CAUSES
    # MOST COMMON FIRST
    # ============================================================

    root_causes = dict(
        sorted(
            root_causes.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )

    # ============================================================
    # SORT EXCEPTIONS
    # ============================================================

    exceptions = dict(
        sorted(
            exceptions.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )

    # ============================================================
    # SORT COMPONENTS
    # ============================================================

    components = dict(
        sorted(
            components.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )

    # ============================================================
    # DASHBOARD
    # ============================================================

    dashboard = {

        "total_bugs":
            total,

        "resolved_bugs":
            resolved,

        "unresolved_bugs":
            unresolved,

        "verified_bugs":
            len(
                load_verified_bugs()
            ),

        "average_confidence":
            average_confidence,

        "duplicate_bugs":
            bugs_with_matches,

        "bugs_with_matches":
            bugs_with_matches,

        "average_duplicate_matches":
            average_matches,

        "average_matches":
            average_matches,

        "severity":
            severity,

        "priority":
            priority,

        "components":
            components,

        "exceptions":
            exceptions,

        "root_causes":
            root_causes
    }

    # ============================================================
    # RENDER EXISTING UI
    # ============================================================

    return render_template(
        "analytics.html",

        dashboard=dashboard,

        reports=reports,

        total_bugs=total,

        resolved_bugs=resolved,

        unresolved_bugs=unresolved,

        verified_bugs=
            len(
                load_verified_bugs()
            )
    )

     


# ============================================================
# MARK BUG AS RESOLVED
# ============================================================

@app.route(
    "/mark-resolved/<bug_id>",
    methods=["POST"]
)
def mark_resolved(
    bug_id
):

    json_path = get_analysis_path(
        bug_id
    )

    analysis = load_json_file(
        json_path,
        None
    )

    if not isinstance(
        analysis,
        dict
    ):

        return jsonify({
            "success":
                False,

            "message":
                "Analysis report was not found."
        }), 404

    if analysis.get(
        "resolved",
        False
    ):

        return jsonify({
            "success":
                True,

            "message":
                "This bug is already in the knowledge base."
        })

    triage = analysis.get(
        "triage",
        {}
    )

    if not isinstance(
        triage,
        dict
    ):
        triage = {}

    root = analysis.get(
        "root_cause_analysis",
        {}
    )

    if not isinstance(
        root,
        dict
    ):
        root = {}

    remediation = analysis.get(
        "remediation",
        {}
    )

    if not isinstance(
        remediation,
        dict
    ):
        remediation = {}

    steps = remediation.get(
        "recommended_steps",
        remediation.get(
            "steps",
            []
        )
    )

    if isinstance(
        steps,
        list
    ):

        resolution = " ".join(
            clean_text(x)
            for x in steps
            if clean_text(x)
        )

    else:

        resolution = clean_text(
            steps
        )

    if not resolution:

        resolution = (
            "Apply the recommended fix "
            "and perform regression testing."
        )

    bugs = load_verified_bugs()

    already_exists = any(
        isinstance(item, dict)
        and str(
            item.get("bug_id")
        ) == str(bug_id)
        for item in bugs
    )

    if not already_exists:

        bugs.append({
            "bug_id":
                str(bug_id),

            "bug_title":
                analysis.get(
                    "bug_title",
                    "Resolved Bug"
                ),

            "bug_report":
                analysis.get(
                    "bug_report",
                    ""
                ),

            "severity":
                triage.get(
                    "severity",
                    "Unknown"
                ),

            "root_cause":
                root.get(
                    "root_cause",
                    ""
                ),

            "resolution":
                resolution,

            "component":
                triage.get(
                    "component",
                    "Unknown"
                ),

            "verified":
                True,

            "verified_at":
                datetime.now().isoformat()
        })

    if not save_verified_bugs(
        bugs
    ):

        return jsonify({
            "success":
                False,

            "message":
                "Could not save the verified bug."
        }), 500

    index_updated = (
        rebuild_knowledge_base_index()
    )

    analysis["resolved"] = True

    analysis["resolved_at"] = (
        datetime.now().isoformat()
    )

    analysis["knowledge_base_added"] = True

    save_json_file(
        json_path,
        analysis
    )

    reports = load_bug_reports()

    for report in reports:

        if (
            isinstance(
                report,
                dict
            )
            and
            str(
                report.get(
                    "bug_id"
                )
            )
            == str(bug_id)
        ):

            report["resolved"] = True

            report["resolved_at"] = (
                datetime.now().isoformat()
            )

            report["knowledge_base_added"] = True

    save_bug_reports(
        reports
    )

    return jsonify({
        "success":
            True,

        "message":
            (
                "Bug marked as resolved and added "
                "to the historical knowledge base."
                if index_updated
                else
                "Bug added to the knowledge base. "
                "FAISS index was not rebuilt."
            ),

        "bug_id":
            str(bug_id),

        "total_verified_bugs":
            len(bugs),

        "index_updated":
            index_updated
    })



# ============================================================
# KNOWLEDGE BASE API
# ============================================================

@app.route(
    "/api/knowledge-base"
)
def knowledge_base_api():

    bugs = load_verified_bugs()

    return jsonify({
        "success":
            True,

        "count":
            len(bugs),

        "bugs":
            bugs[-50:]
    })


# ============================================================
# REBUILD KNOWLEDGE BASE
# ============================================================

@app.route(
    "/rebuild-knowledge-base",
    methods=["POST"]
)
def rebuild_knowledge_base():

    success = (
        rebuild_knowledge_base_index()
    )

    return jsonify({
        "success":
            success,

        "message":
            (
                "Knowledge base FAISS index rebuilt successfully."
                if success
                else
                "Knowledge base index could not be rebuilt."
            ),

        "count":
            len(
                load_verified_bugs()
            )
    }), (
        200
        if success
        else 500
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)
def health():

    return jsonify({
        "status":
            "running",

        "application":
            "Creation of Intelligent Bug Diagnosis Platform",

        "version":
            "3.0",

        "milestone":
            "Milestone 3",

        "sentence_transformer":
            embedding_model is not None,

        "faiss":
            faiss is not None,

        "knowledge_base":
            len(
                load_verified_bugs()
            )
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return render_template(
        "index.html"
    ), 404


@app.errorhandler(500)
def server_error(error):

    print(
        "Internal Server Error:",
        error
    )

    return (
        "<h2>Something went wrong.</h2>"
        "<p>Check the Flask terminal for the exact error.</p>"
        '<p><a href="/">Return to Home</a></p>',
        500
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(
        "Creation of Intelligent Bug Diagnosis Platform"
    )
    print(
        "Application Ready"
    )
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )