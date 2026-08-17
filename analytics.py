import os
import json
from collections import Counter

# ============================================================
# CONFIGURATION
# ============================================================

ANALYSIS_FOLDER = "analysis_results"

# Possible locations used by the project
KNOWLEDGE_BASE_FILES = [
    os.path.join(
        "dataset",
        "growth_knowledge_base",
        "verified_bugs.json"
    ),
    os.path.join(
        "dataset",
        "growth_knowledge_base",
        "verified_bugs.csv"
    ),
    os.path.join(
        "verified_knowledge_base",
        "verified_bugs.json"
    ),
]

FAISS_INDEX_FILES = [
    os.path.join(
        "dataset",
        "growth_knowledge_base",
        "verified_bugs.faiss"
    ),
    os.path.join(
        "verified_knowledge_base",
        "verified_bugs.faiss"
    ),
]


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_confidence(value):
    """
    Converts:
        0.91 -> 91
        91   -> 91
    """
    value = safe_float(value, 0)

    if value <= 1:
        value *= 100

    return max(0, min(100, value))


def normalize_component(component):
    """
    Convert different names of the same component
    into one common category.
    """

    if not component:
        return "Unknown"

    component = str(component).strip()

    key = component.lower()

    mapping = {
        "login module": "Authentication",
        "login system": "Authentication",
        "login functionality": "Authentication",
        "login feature": "Authentication",
        "login page": "Authentication",
        "login page component": "Authentication",
        "authentication module": "Authentication",
        "authentication service": "Authentication",
        "login controller": "Authentication",
        "logincontroller": "Authentication",
        "loginservice": "Authentication",
        "login service": "Authentication",
        "login api": "Authentication",
        "login/authenticate": "Authentication",
        "authentication": "Authentication",
        "auth": "Authentication",

        "ui": "User Interface",
        "user interface": "User Interface",
        "frontend": "User Interface",
        "front end": "User Interface",

        "database": "Database",
        "db": "Database",

        "payment": "Payment",
        "payments": "Payment",

        "network": "Network",
        "api": "API",
        "backend": "Backend",
    }

    return mapping.get(key, component)


def normalize_exception(exception):
    """
    Normalize Java exception names.
    """

    if not exception:
        return "UnknownException"

    value = str(exception).strip()

    if not value:
        return "UnknownException"

    if value.endswith("NullPointerException"):
        return "NullPointerException"

    if value.endswith("IllegalArgumentException"):
        return "IllegalArgumentException"

    if value.endswith("IndexOutOfBoundsException"):
        return "IndexOutOfBoundsException"

    if value.endswith("SQLException"):
        return "SQLException"

    if value.endswith("IOException"):
        return "IOException"

    return value


# ============================================================
# ROOT CAUSE PATTERN NORMALIZATION
# ============================================================

def normalize_root_cause(root_cause):
    """
    Converts long AI-generated root-cause sentences into
    meaningful recurring defect patterns.

    This prevents Analytics from treating every slightly
    different AI sentence as a completely different pattern.
    """

    if not root_cause:
        return None

    text = str(root_cause).strip()

    if not text:
        return None

    value = text.lower()

    # Ignore generic / empty AI responses
    generic_patterns = [
        "no sufficiently similar historical root cause",
        "requires further investigation",
        "recommended corrective action",
        "no historical root cause",
        "unknown root cause",
        "root cause could not be determined",
    ]

    if any(
        pattern in value
        for pattern in generic_patterns
    ):
        return "Further Investigation Required"

    # Null related defects
    if (
        "nullpointerexception" in value
        or "null pointer" in value
        or "is null" in value
        or "was null" in value
        or "null before" in value
    ):
        return "Null Handling / Input Validation"

    # Authentication
    if (
        "authentication" in value
        or "username" in value
        or "password" in value
        or "login" in value
        or "authorization" in value
    ):
        return "Authentication / Login Validation"

    # Database
    if (
        "database" in value
        or "sql" in value
        or "query" in value
        or "repository" in value
    ):
        return "Database / Query Handling"

    # Input validation
    if (
        "input validation" in value
        or "validate input" in value
        or "invalid input" in value
        or "user input" in value
    ):
        return "Input Validation"

    # Exception handling
    if (
        "exception handling" in value
        or "exception" in value
        or "error handling" in value
    ):
        return "Exception Handling"

    # API
    if (
        "api" in value
        or "request" in value
        or "response" in value
        or "endpoint" in value
    ):
        return "API / Request Handling"

    # UI
    if (
        "user interface" in value
        or "frontend" in value
        or "ui" in value
        or "page" in value
    ):
        return "User Interface"

    # Security
    if (
        "security" in value
        or "permission" in value
        or "access control" in value
    ):
        return "Security / Access Control"

    # Testing
    if (
        "test" in value
        or "regression" in value
    ):
        return "Testing / Regression Coverage"

    # Fallback:
    # Keep short unknown causes instead of huge paragraphs.
    if len(text) > 100:
        return text[:100].rstrip() + "..."

    return text


# ============================================================
# LOAD JSON SAFELY
# ============================================================

def load_json(path):
    try:
        if not os.path.exists(path):
            return None

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:
        return None


# ============================================================
# KNOWLEDGE BASE GROWTH
# ============================================================

def find_verified_knowledge_base():
    """
    Find the verified bug knowledge-base file.
    """

    for path in KNOWLEDGE_BASE_FILES:

        if os.path.exists(path):

            return path

    return None


def get_verified_bugs():
    """
    Load bugs that were explicitly marked as resolved
    and added to the growth knowledge base.
    """

    path = find_verified_knowledge_base()

    if not path:
        return []

    # JSON knowledge base
    if path.lower().endswith(".json"):

        data = load_json(path)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            for key in [
                "bugs",
                "verified_bugs",
                "data",
                "items"
            ]:

                value = data.get(key)

                if isinstance(value, list):
                    return value

    return []


def get_knowledge_base_count():
    """
    Number of verified bugs stored in the growth KB.
    """

    bugs = get_verified_bugs()

    return len(bugs)


def get_knowledge_base_index_count():
    """
    Number of vectors currently stored in the FAISS
    growth knowledge-base index.
    """

    for path in FAISS_INDEX_FILES:

        if not os.path.exists(path):
            continue

        try:

            import faiss

            index = faiss.read_index(path)

            return int(index.ntotal)

        except Exception:

            return 0

    return 0


def get_knowledge_base_growth_rate(
    total_bugs,
    verified_bugs
):
    """
    Percentage of analyzed bugs that became verified
    knowledge-base entries.
    """

    if total_bugs <= 0:
        return 0

    return round(
        (verified_bugs / total_bugs) * 100,
        2
    )


# ============================================================
# MAIN ANALYTICS FUNCTION
# ============================================================

def get_dashboard_data():

    severity_counter = Counter()
    component_counter = Counter()
    exception_counter = Counter()
    rootcause_counter = Counter()

    priority_counter = Counter()

    total_confidence = 0
    confidence_count = 0

    total_bugs = 0

    resolved_bugs = 0
    open_bugs = 0

    duplicate_bugs = 0
    total_duplicate_matches = 0

    # --------------------------------------------------------
    # ANALYSIS DIRECTORY
    # --------------------------------------------------------

    if not os.path.exists(
        ANALYSIS_FOLDER
    ):

        return {
            "total_bugs": 0,
            "average_confidence": 0,
            "severity": {},
            "components": {},
            "exceptions": {},
            "root_causes": {},
            "duplicate_bugs": 0,
            "average_duplicate_matches": 0,
            "resolved_bugs": 0,
            "open_bugs": 0,
            "resolution_rate": 0,
            "priority": {},
            "knowledge_base": {
                "verified_bugs": 0,
                "indexed_vectors": 0,
                "growth_rate": 0,
                "index_status": "NOT AVAILABLE"
            }
        }

    files = [
        f
        for f in os.listdir(
            ANALYSIS_FOLDER
        )
        if f.lower().endswith(".json")
    ]

    # --------------------------------------------------------
    # PROCESS EVERY ANALYSIS
    # --------------------------------------------------------

    for filename in files:

        filepath = os.path.join(
            ANALYSIS_FOLDER,
            filename
        )

        data = load_json(filepath)

        if not isinstance(
            data,
            dict
        ):
            continue

        total_bugs += 1

        # ====================================================
        # TRIAGE
        # ====================================================

        triage = data.get(
            "triage",
            {}
        )

        if not isinstance(
            triage,
            dict
        ):
            triage = {}

        severity = str(
            triage.get(
                "severity",
                "Unknown"
            )
            or "Unknown"
        )

        component = normalize_component(
            triage.get(
                "component",
                "Unknown"
            )
        )

        priority = str(
            triage.get(
                "priority",
                "Unknown"
            )
            or "Unknown"
        )

        confidence = normalize_confidence(
            triage.get(
                "confidence",
                0
            )
        )

        severity_counter[
            severity
        ] += 1

        component_counter[
            component
        ] += 1

        priority_counter[
            priority
        ] += 1

        if confidence > 0:

            total_confidence += confidence

            confidence_count += 1

        # ====================================================
        # RESOLUTION STATUS
        # ====================================================

        is_resolved = bool(
            data.get(
                "resolved",
                False
            )
        )

        if is_resolved:

            resolved_bugs += 1

        else:

            open_bugs += 1

        # ====================================================
        # LOG ANALYSIS
        # ====================================================

        log = data.get(
            "log_analysis",
            {}
        )

        if not isinstance(
            log,
            dict
        ):
            log = {}

        exception = normalize_exception(
            log.get(
                "exception_type",
                "UnknownException"
            )
        )

        exception_counter[
            exception
        ] += 1

        # ====================================================
        # ROOT CAUSE
        # ====================================================

        causes_found = []

        # ---- AI FIX ROOT CAUSE ----

        ai_fix = data.get(
            "ai_fix",
            {}
        )

        if isinstance(
            ai_fix,
            dict
        ):

            raw_causes = ai_fix.get(
                "root_cause",
                []
            )

            if isinstance(
                raw_causes,
                str
            ):
                raw_causes = [
                    raw_causes
                ]

            if isinstance(
                raw_causes,
                list
            ):

                causes_found.extend(
                    raw_causes
                )

        # ---- ROOT CAUSE ANALYSIS ----

        root_analysis = data.get(
            "root_cause_analysis",
            {}
        )

        if isinstance(
            root_analysis,
            dict
        ):

            root = root_analysis.get(
                "root_cause",
                ""
            )

            if root:
                causes_found.append(
                    root
                )

        # ---- DEDUPLICATE PATTERNS ----

        patterns_in_bug = set()

        for cause in causes_found:

            pattern = normalize_root_cause(
                cause
            )

            if pattern:

                patterns_in_bug.add(
                    pattern
                )

        for pattern in patterns_in_bug:

            rootcause_counter[
                pattern
            ] += 1

        # ====================================================
        # DUPLICATE DETECTION
        # ====================================================

        duplicates = data.get(
            "similar_bugs",
            []
        )

        if not isinstance(
            duplicates,
            list
        ):
            duplicates = []

        if duplicates:

            duplicate_bugs += 1

            total_duplicate_matches += len(
                duplicates
            )

    # ========================================================
    # CALCULATIONS
    # ========================================================

    if confidence_count > 0:

        average_confidence = round(
            total_confidence /
            confidence_count,
            2
        )

    else:

        average_confidence = 0

    if duplicate_bugs > 0:

        average_duplicate_matches = round(
            total_duplicate_matches /
            duplicate_bugs,
            2
        )

    else:

        average_duplicate_matches = 0

    if total_bugs > 0:

        resolution_rate = round(
            (
                resolved_bugs /
                total_bugs
            ) * 100,
            2
        )

    else:

        resolution_rate = 0

    # ========================================================
    # KNOWLEDGE BASE GROWTH
    # ========================================================

    verified_count = (
        get_knowledge_base_count()
    )

    indexed_count = (
        get_knowledge_base_index_count()
    )

    growth_rate = (
        get_knowledge_base_growth_rate(
            total_bugs,
            verified_count
        )
    )

    if indexed_count > 0:

        index_status = "READY"

    else:

        index_status = "NOT AVAILABLE"

    # ========================================================
    # RETURN DASHBOARD
    # ========================================================

    dashboard = {

        # Existing fields - KEEP THESE
        "total_bugs":
            total_bugs,

        "average_confidence":
            average_confidence,

        "severity":
            dict(
                severity_counter
            ),

        "components":
            dict(
                component_counter
            ),

        "exceptions":
            dict(
                exception_counter
            ),

        "root_causes":
            dict(
                rootcause_counter
            ),

        "duplicate_bugs":
            duplicate_bugs,

        "average_duplicate_matches":
            average_duplicate_matches,

        # New Milestone 4 fields
        "resolved_bugs":
            resolved_bugs,

        "open_bugs":
            open_bugs,

        "resolution_rate":
            resolution_rate,

        "priority":
            dict(
                priority_counter
            ),

        "knowledge_base":
            {
                "verified_bugs":
                    verified_count,

                "indexed_vectors":
                    indexed_count,

                "growth_rate":
                    growth_rate,

                "index_status":
                    index_status
            },

        # Convenient top-level values
        # for future HTML use
        "verified_bugs":
            verified_count,

        "indexed_vectors":
            indexed_count,

        "knowledge_base_growth_rate":
            growth_rate,

        "knowledge_base_index_status":
            index_status
    }

    return dashboard


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    dashboard = get_dashboard_data()

    print()
    print("=" * 60)
    print("DEFECT PATTERN ANALYTICS")
    print("=" * 60)

    print()
    print(
        "Total Bugs:",
        dashboard["total_bugs"]
    )

    print(
        "Resolved Bugs:",
        dashboard["resolved_bugs"]
    )

    print(
        "Open Bugs:",
        dashboard["open_bugs"]
    )

    print(
        "Resolution Rate:",
        str(
            dashboard["resolution_rate"]
        ) + "%"
    )

    print(
        "Average AI Confidence:",
        str(
            dashboard["average_confidence"]
        ) + "%"
    )

    print()
    print("-" * 60)
    print("KNOWLEDGE BASE GROWTH")
    print("-" * 60)

    kb = dashboard[
        "knowledge_base"
    ]

    print(
        "Verified Bugs:",
        kb["verified_bugs"]
    )

    print(
        "FAISS Indexed Vectors:",
        kb["indexed_vectors"]
    )

    print(
        "Knowledge Base Growth Rate:",
        str(
            kb["growth_rate"]
        ) + "%"
    )

    print(
        "FAISS Index Status:",
        kb["index_status"]
    )

    print()
    print("-" * 60)
    print("SEVERITY DISTRIBUTION")
    print("-" * 60)

    for key, value in dashboard[
        "severity"
    ].items():

        print(
            f"{key}: {value}"
        )

    print()
    print("-" * 60)
    print("AFFECTED COMPONENTS")
    print("-" * 60)

    for key, value in dashboard[
        "components"
    ].items():

        print(
            f"{key}: {value}"
        )

    print()
    print("-" * 60)
    print("EXCEPTION TYPES")
    print("-" * 60)

    for key, value in dashboard[
        "exceptions"
    ].items():

        print(
            f"{key}: {value}"
        )

    print()
    print("-" * 60)
    print("ROOT CAUSE PATTERNS")
    print("-" * 60)

    for key, value in dashboard[
        "root_causes"
    ].items():

        print(
            f"{key}: {value}"
        )

    print()
    print("-" * 60)
    print("PRIORITY DISTRIBUTION")
    print("-" * 60)

    for key, value in dashboard[
        "priority"
    ].items():

        print(
            f"{key}: {value}"
        )

    print()
    print("-" * 60)
    print("DUPLICATE ANALYSIS")
    print("-" * 60)

    print(
        "Bugs with historical matches:",
        dashboard["duplicate_bugs"]
    )

    print(
        "Average historical matches:",
        dashboard[
            "average_duplicate_matches"
        ]
    )

    print("=" * 60)
    print()