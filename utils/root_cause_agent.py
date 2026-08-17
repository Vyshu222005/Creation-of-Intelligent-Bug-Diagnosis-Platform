"""
Hybrid Root Cause Analysis Agent

Uses:
    1. Structured log/stack-trace evidence
    2. Sentence-Transformer semantic search
    3. FAISS historical defect evidence
    4. Similarity-weighted confidence

No Gemini API.
No external API.
No hard-coded error -> answer rules.

The module keeps a simple generate_root_cause()
interface so existing app.py code can continue using it.
"""

from .hybrid_engine import semantic_search, clean_text


# ============================================================
# HELPERS
# ============================================================

def _safe_dict(value):
    """Return a dictionary or an empty dictionary."""
    return value if isinstance(value, dict) else {}


def _safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        number = float(value)

        # Convert 0.85 -> 85
        if 0 <= number <= 1:
            number *= 100

        return number

    except (TypeError, ValueError):
        return default


def _extract_log_evidence(log_analysis):
    """
    Extract useful evidence produced by the Log Analysis Agent.
    """

    log_analysis = _safe_dict(log_analysis)

    exception_type = clean_text(
        log_analysis.get(
            "exception_type",
            ""
        )
    )

    failure_point = clean_text(
        log_analysis.get(
            "failure_point",
            ""
        )
    )

    code_path = clean_text(
        log_analysis.get(
            "code_path",
            ""
        )
    )

    error_message = clean_text(
        log_analysis.get(
            "error_message",
            ""
        )
    )

    root_cause = clean_text(
        log_analysis.get(
            "root_cause",
            ""
        )
    )

    return {
        "exception_type": exception_type,
        "failure_point": failure_point,
        "code_path": code_path,
        "error_message": error_message,
        "root_cause": root_cause
    }


# ============================================================
# HISTORICAL SEMANTIC EVIDENCE
# ============================================================

def _get_historical_evidence(
    bug_text,
    top_k=5
):
    """
    Retrieve historical defects using semantic similarity.

    The actual semantic search is performed by the existing
    Sentence-Transformer + FAISS pipeline.
    """

    try:
        results = semantic_search(
            bug_text,
            top_k=top_k
        )

    except Exception:
        return []

    if not isinstance(results, list):
        return []

    evidence = []

    for item in results:

        if not isinstance(item, dict):
            continue

        similarity = _safe_float(
            item.get(
                "similarity",
                item.get(
                    "score",
                    0
                )
            )
        )

        historical_root = clean_text(
            item.get(
                "root_cause",
                ""
            )
        )

        resolution = clean_text(
            item.get(
                "resolution",
                ""
            )
        )

        bug_report = clean_text(
            item.get(
                "bug_report",
                item.get(
                    "description",
                    ""
                )
            )
        )

        bug_title = clean_text(
            item.get(
                "bug_title",
                item.get(
                    "title",
                    "Historical Bug"
                )
            )
        )

        evidence.append({
            "bug_title": bug_title,
            "root_cause": historical_root,
            "resolution": resolution,
            "bug_report": bug_report,
            "similarity": similarity
        })

    evidence.sort(
        key=lambda item:
            item.get(
                "similarity",
                0
            ),
        reverse=True
    )

    return evidence


# ============================================================
# HYBRID ROOT CAUSE GENERATION
# ============================================================

def generate_root_cause(
    bug_text,
    log_analysis,
    historical_matches=None
):
    """
    Generate a hybrid root-cause analysis.

    Hybrid evidence:

        Log Analysis
              +
        FAISS semantic retrieval
              +
        similarity weighting
              =
        Root Cause Analysis

    No Gemini API is used.
    """

    bug_text = clean_text(
        bug_text
    )

    log_evidence = _extract_log_evidence(
        log_analysis
    )

    # --------------------------------------------------------
    # Retrieve historical evidence if app.py did not provide it
    # --------------------------------------------------------

    if historical_matches is None:

        historical_matches = (
            _get_historical_evidence(
                bug_text,
                top_k=5
            )
        )

    elif not isinstance(
        historical_matches,
        list
    ):

        historical_matches = []

    # --------------------------------------------------------
    # Keep only valid historical evidence
    # --------------------------------------------------------

    historical_evidence = []

    for item in historical_matches:

        if not isinstance(item, dict):
            continue

        similarity = _safe_float(
            item.get(
                "similarity",
                item.get(
                    "score",
                    0
                )
            )
        )

        root = clean_text(
            item.get(
                "root_cause",
                ""
            )
        )

        if root or similarity > 0:

            historical_evidence.append({
                "root_cause": root,
                "resolution": clean_text(
                    item.get(
                        "resolution",
                        ""
                    )
                ),
                "bug_title": clean_text(
                    item.get(
                        "bug_title",
                        "Historical Bug"
                    )
                ),
                "similarity": similarity
            })

    historical_evidence.sort(
        key=lambda x:
            x["similarity"],
        reverse=True
    )

    # --------------------------------------------------------
    # Strongest historical match
    # --------------------------------------------------------

    best_historical = (
        historical_evidence[0]
        if historical_evidence
        else None
    )

    historical_similarity = (
        best_historical["similarity"]
        if best_historical
        else 0
    )

    # --------------------------------------------------------
    # Log-analysis evidence
    # --------------------------------------------------------

    log_root_cause = log_evidence[
        "root_cause"
    ]

    exception_type = log_evidence[
        "exception_type"
    ]

    failure_point = log_evidence[
        "failure_point"
    ]

    code_path = log_evidence[
        "code_path"
    ]

    error_message = log_evidence[
        "error_message"
    ]

    # --------------------------------------------------------
    # HYBRID EVIDENCE FUSION
    # --------------------------------------------------------

    evidence_sources = []

    if log_root_cause:
        evidence_sources.append(
            "Log Analysis"
        )

    if exception_type:
        evidence_sources.append(
            "Exception Evidence"
        )

    if failure_point:
        evidence_sources.append(
            "Failure-Point Evidence"
        )

    if historical_evidence:
        evidence_sources.append(
            "FAISS Historical Similarity"
        )

    # --------------------------------------------------------
    # CASE 1:
    # Strong log evidence + historical evidence
    # --------------------------------------------------------

    if (
        log_root_cause
        and
        best_historical
        and
        historical_similarity >= 40
    ):

        root_cause = log_root_cause

        # Weighted evidence fusion
        # Dynamic confidence from the amount of structured log evidence.
        evidence_count = sum([
            bool(exception_type),
            bool(failure_point),
            bool(error_message),
            bool(code_path)
        ])

        if evidence_count >= 4:
            log_confidence = 90
        elif evidence_count == 3:
            log_confidence = 84
        elif evidence_count == 2:
            log_confidence = 76
        elif evidence_count == 1:
            log_confidence = 65
        else:
            log_confidence = 50

        confidence = (
    (0.60 * 82)
    +
    (0.40 * historical_similarity)
)

        reasoning = (
            "Hybrid semantic analysis combined the "
            "Log Analysis Agent's structured failure "
            "evidence with FAISS-retrieved historical "
            f"defect evidence ({historical_similarity:.1f}% similarity)."
        )

        evidence_type = (
            "Log Analysis + FAISS Semantic Evidence"
        )

    # --------------------------------------------------------
    # CASE 2:
    # Log evidence exists but historical evidence is weak
    # --------------------------------------------------------

    elif log_root_cause:

        root_cause = log_root_cause

        # Dynamic confidence based on structured log evidence.
        # This prevents every bug from receiving the same confidence.
        evidence_count = sum([
            bool(exception_type),
            bool(failure_point),
            bool(error_message),
            bool(code_path)
        ])

        if evidence_count >= 4:
            confidence = 88
        elif evidence_count == 3:
            confidence = 82
        elif evidence_count == 2:
            confidence = 74
        elif evidence_count == 1:
            confidence = 64
        else:
            confidence = 50

        # Historical evidence can increase confidence slightly.
        if historical_similarity > 0:
            confidence += min(8, historical_similarity * 0.10)

        reasoning = (
            "The root cause was derived from structured "
            "stack-trace and error evidence. Historical "
            "semantic matches were insufficient to strongly "
            "support the diagnosis."
        )

        evidence_type = (
            "Log Analysis + Semantic Search"
        )

    # --------------------------------------------------------
    # CASE 3:
    # No log root cause but strong historical evidence
    # --------------------------------------------------------

    elif (
        best_historical
        and
        historical_similarity >= 50
    ):

        root_cause = best_historical[
            "root_cause"
        ]

        confidence = max(
            50,
            min(
                90,
                historical_similarity
            )
        )

        reasoning = (
            "The root cause was inferred from the most "
            "semantically similar historical defects "
            f"retrieved through FAISS ({historical_similarity:.1f}% similarity)."
        )

        evidence_type = (
            "FAISS Historical Semantic Evidence"
        )

    # --------------------------------------------------------
    # CASE 4:
    # Log analysis itself contains useful technical evidence
    # --------------------------------------------------------

    elif (
        exception_type
        or
        failure_point
        or
        error_message
    ):

        parts = []

        if exception_type:
            parts.append(
                f"{exception_type}"
            )

        if error_message:
            parts.append(
                error_message
            )

        if failure_point:
            parts.append(
                f"Failure occurs at {failure_point}."
            )

        root_cause = " ".join(
            parts
        )

        confidence = 70

        reasoning = (
            "Root-cause evidence was extracted from "
            "the submitted failure information."
        )

        evidence_type = (
            "Structured Failure Evidence"
        )

    # --------------------------------------------------------
    # CASE 5:
    # Insufficient evidence
    # --------------------------------------------------------

    else:

        root_cause = (
            "The submitted defect does not contain "
            "sufficient evidence to determine the exact "
            "root cause."
        )

        confidence = 40

        reasoning = (
            "Insufficient log and historical semantic "
            "evidence was available."
        )

        evidence_type = (
            "Insufficient Evidence"
        )

    # --------------------------------------------------------
    # Confidence normalization
    # --------------------------------------------------------

    confidence = int(
        max(
            40,
            min(
                95,
                round(
                    confidence
                )
            )
        )
    )

    # --------------------------------------------------------
    # Supporting evidence
    # --------------------------------------------------------

    supporting_evidence = []

    if exception_type:

        supporting_evidence.append(
            f"Exception: {exception_type}"
        )

    if error_message:

        supporting_evidence.append(
            f"Error message: {error_message}"
        )

    if failure_point:

        supporting_evidence.append(
            f"Failure point: {failure_point}"
        )

    if code_path:

        supporting_evidence.append(
            f"Code path: {code_path}"
        )

    if best_historical:

        supporting_evidence.append(
            "Best historical similarity: "
            f"{historical_similarity:.1f}%"
        )

    # --------------------------------------------------------
    # Return structure
    # --------------------------------------------------------

    return {

        "root_cause":
            clean_text(
                root_cause
            ),

        "confidence":
            confidence,

        "reasoning":
            reasoning,

        "evidence_type":
            evidence_type,

        "evidence_sources":
            evidence_sources,

        "supporting_evidence":
            supporting_evidence,

        "historical_evidence":
            historical_evidence[:3]
    }


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def analyze_root_cause(
    bug_text,
    log_analysis,
    historical_matches=None
):
    """
    Compatibility wrapper.

    Allows app.py to call either:
        generate_root_cause()
    or:
        analyze_root_cause()
    """

    return generate_root_cause(
        bug_text,
        log_analysis,
        historical_matches
    )