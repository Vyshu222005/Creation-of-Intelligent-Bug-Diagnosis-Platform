from .hybrid_engine import semantic_search, clean_text


def generate_remediation(
    bug_text,
    triage,
    log_analysis,
    root_cause
):
    """
    Generate concise remediation recommendations using:
    1. Root-cause evidence
    2. Log analysis
    3. Historical FAISS similarity

    The output is intentionally deduplicated so that the
    Remediation Plan does not repeat the same sentence.
    """

    # ---------------------------------------------------------
    # 1. SEARCH HISTORICAL BUGS
    # ---------------------------------------------------------

    try:
        historical = semantic_search(
            bug_text,
            top_k=5
        )
    except Exception:
        historical = []

    resolutions = []

    for bug in historical:

        if not isinstance(bug, dict):
            continue

        resolution = clean_text(
            bug.get("resolution", "")
        )

        similarity = bug.get(
            "similarity",
            0
        )

        try:
            similarity = float(similarity)
        except (TypeError, ValueError):
            similarity = 0

        if resolution:
            resolutions.append(
                {
                    "resolution": resolution,
                    "similarity": similarity
                }
            )

    # ---------------------------------------------------------
    # 2. SORT HISTORICAL RESOLUTIONS
    # ---------------------------------------------------------

    resolutions.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    # ---------------------------------------------------------
    # 3. REMOVE DUPLICATE RESOLUTIONS
    # ---------------------------------------------------------

    recommended = []
    seen = set()

    for item in resolutions:

        resolution = item["resolution"]

        # Normalize text for duplicate comparison
        key = " ".join(
            resolution.lower().split()
        )

        if key not in seen:

            seen.add(key)

            recommended.append(
                resolution
            )

        if len(recommended) >= 4:
            break

    # ---------------------------------------------------------
    # 4. EXTRACT LOG INFORMATION
    # ---------------------------------------------------------

    exception_type = ""

    if isinstance(log_analysis, dict):

        exception_type = clean_text(
            log_analysis.get(
                "exception_type",
                ""
            )
        )

    # ---------------------------------------------------------
    # 5. EXTRACT TRIAGE INFORMATION
    # ---------------------------------------------------------

    component = "Unknown"
    priority = "Unknown"

    if isinstance(triage, dict):

        component = clean_text(
            triage.get(
                "component",
                "Unknown"
            )
        )

        priority = clean_text(
            triage.get(
                "priority",
                "Unknown"
            )
        )

    # ---------------------------------------------------------
    # 6. EXTRACT ROOT CAUSE
    # ---------------------------------------------------------

    root_cause_text = ""

    if isinstance(root_cause, dict):

        root_cause_text = clean_text(
            root_cause.get(
                "root_cause",
                ""
            )
        )

    elif isinstance(root_cause, str):

        root_cause_text = clean_text(
            root_cause
        )

    if not root_cause_text:

        root_cause_text = (
            "The defect requires further investigation "
            "based on the available evidence."
        )

    # ---------------------------------------------------------
    # 7. ADD TECHNICAL RECOMMENDATIONS
    # ---------------------------------------------------------

    technical_steps = []

    # NullPointerException
    if (
        "nullpointerexception"
        in exception_type.lower()
    ):

        technical_steps.extend(
            [
                "Validate objects and input values before accessing them.",
                "Add null checks and safe exception handling.",
                "Add regression tests for null and missing-input scenarios."
            ]
        )

    # Authentication bugs
    if (
        "authentication"
        in component.lower()
        or
        "login"
        in bug_text.lower()
    ):

        technical_steps.extend(
            [
                "Validate username and password before authentication.",
                "Handle invalid or missing user credentials safely.",
                "Add regression tests for invalid login attempts."
            ]
        )

    # Generic fallback
    if not technical_steps:

        technical_steps.extend(
            [
                "Validate all inputs before processing.",
                "Add appropriate exception handling around the failing operation.",
                "Apply the corrective change and verify the affected code path.",
                "Run functional and regression tests."
            ]
        )

    # ---------------------------------------------------------
    # 8. COMBINE HISTORICAL + TECHNICAL STEPS
    # ---------------------------------------------------------

    all_steps = []

    for step in technical_steps:
        all_steps.append(step)

    for resolution in recommended:
        all_steps.append(resolution)

    # ---------------------------------------------------------
    # 9. FINAL DEDUPLICATION
    # ---------------------------------------------------------

    final_steps = []
    final_seen = set()

    for step in all_steps:

        step = clean_text(step)

        if not step:
            continue

        key = " ".join(
            step.lower().split()
        )

        if key not in final_seen:

            final_seen.add(key)

            final_steps.append(step)

    # Keep report concise
    final_steps = final_steps[:6]

    # ---------------------------------------------------------
    # 10. TESTING PLAN
    # ---------------------------------------------------------

    testing = [
        "Run functional testing for the affected feature.",
        "Run regression testing for related functionality.",
        "Run integration testing where applicable."
    ]

    # Add specific test for NullPointerException
    if (
        "nullpointerexception"
        in exception_type.lower()
    ):

        testing.insert(
            0,
            "Test null, empty and missing input values."
        )

    # Remove duplicates
    testing = list(
        dict.fromkeys(testing)
    )

    # ---------------------------------------------------------
    # 11. PREVENTION PLAN
    # ---------------------------------------------------------

    prevention = [
        "Add regression tests for the confirmed defect.",
        "Improve input validation and exception handling.",
        "Monitor the affected component after deployment."
    ]

    # ---------------------------------------------------------
    # 12. BEST HISTORICAL SIMILARITY
    # ---------------------------------------------------------

    best_similarity = 0

    if resolutions:

        best_similarity = resolutions[0][
            "similarity"
        ]

    # ---------------------------------------------------------
    # 13. CONFIDENCE
    # ---------------------------------------------------------

    try:

        root_confidence = float(
            root_cause.get(
                "confidence",
                0
            )
            if isinstance(root_cause, dict)
            else 0
        )

    except (TypeError, ValueError):

        root_confidence = 0

    if root_confidence <= 1:
        root_confidence *= 100

    # Combine root-cause confidence and
    # historical similarity.

    if root_confidence > 0:

        confidence = (
            (0.60 * root_confidence)
            +
            (0.40 * best_similarity)
        )

    else:

        confidence = best_similarity

    confidence = int(
        max(
            40,
            min(
                95,
                round(confidence)
            )
        )
    )

    # ---------------------------------------------------------
    # 14. RETURN FINAL REMEDIATION RESULT
    # ---------------------------------------------------------

    return {

        "summary": root_cause_text,

        "recommended_steps": final_steps,

        "steps": final_steps,

        "testing": testing,

        "prevention": prevention,

        "confidence": confidence,

        "component": component,

        "priority": priority,

        "historical_similarity": round(
            best_similarity,
            2
        ),

        "evidence": [
            {
                "similarity": item["similarity"],
                "resolution": item["resolution"]
            }
            for item in resolutions[:3]
        ]
    }