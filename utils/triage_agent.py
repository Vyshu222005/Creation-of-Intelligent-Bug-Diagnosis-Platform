from collections import defaultdict

from .hybrid_engine import (
    semantic_search,
    clean_text
)


SEVERITY_ORDER = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1
}


PRIORITY_ORDER = {
    "P1": 4,
    "P2": 3,
    "P3": 2,
    "P4": 1
}


def weighted_vote(
    bugs,
    field,
    default
):

    scores = defaultdict(float)

    for bug in bugs:

        value = clean_text(
            bug.get(
                field,
                ""
            )
        )

        similarity = float(
            bug.get(
                "similarity",
                0
            )
            or 0
        )

        if not value:
            continue

        scores[value] += (
            similarity / 100.0
        )

    if not scores:
        return default

    return max(
        scores,
        key=scores.get
    )


def confidence_from_evidence(
    bugs
):

    if not bugs:
        return 35

    similarities = [

        float(
            x.get(
                "similarity",
                0
            )
            or 0
        )

        for x in bugs
    ]

    best = max(
        similarities
    )

    average = sum(
        similarities
    ) / len(
        similarities
    )

    confidence = (
        0.65 * best
        +
        0.35 * average
    )

    return int(
        max(
            35,
            min(
                98,
                confidence
            )
        )
    )


def triage_bug(
    bug_text,
    historical_bugs=None
):

    if historical_bugs is None:
        historical_bugs = semantic_search(
            bug_text,
            top_k=5
        )

    bugs = historical_bugs[:5]

    # --------------------------------------------------
    # SEVERITY
    # --------------------------------------------------

    severity = weighted_vote(
        bugs,
        "severity",
        "Medium"
    )

    # --------------------------------------------------
    # COMPONENT
    # --------------------------------------------------

    component = weighted_vote(
        bugs,
        "component",
        "Unknown"
    )

    # --------------------------------------------------
    # PRIORITY
    # --------------------------------------------------

    priority = weighted_vote(
        bugs,
        "priority",
        ""
    )

    # Never allow Unknown/empty priority
    if not priority or priority.lower() == "unknown":

        severity_lower = str(
            severity or ""
        ).lower()

        text_lower = str(
            bug_text or ""
        ).lower()

        # Critical defects
        if (
            severity_lower == "critical"
            or "crash" in text_lower
            or "nullpointerexception" in text_lower
            or "system down" in text_lower
            or "data loss" in text_lower
            or "authentication failure" in text_lower
        ):
            priority = "P1"

        # High defects
        elif severity_lower == "high":
            priority = "P2"

        # Medium defects
        elif severity_lower == "medium":
            priority = "P3"

        # Low defects
        else:
            priority = "P4"

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    confidence = confidence_from_evidence(
        bugs
    )

    # --------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------

    evidence = []

    for bug in bugs[:3]:

        evidence.append(
            {
                "bug_id":
                    bug.get(
                        "bug_id",
                        "Unknown"
                    ),

                "similarity":
                    bug.get(
                        "similarity",
                        0
                    ),

                "severity":
                    bug.get(
                        "severity",
                        "Unknown"
                    ),

                "priority":
                    bug.get(
                        "priority",
                        "Unknown"
                    ),

                "component":
                    bug.get(
                        "component",
                        "Unknown"
                    )
            }
        )

    # --------------------------------------------------
    # REASONING
    # --------------------------------------------------

    reasoning = (
        "Hybrid semantic triage combined "
        "similarity-weighted historical defect "
        "evidence with rule-based priority fallback. "
        "Priority was derived from historical evidence "
        "when available and inferred from severity and "
        "critical failure indicators when historical "
        "priority was unavailable."
    )

    return {

        "severity":
            severity,

        "priority":
            priority,

        "component":
            component,

        "confidence":
            confidence,

        "reasoning":
            reasoning,

        "evidence":
            evidence
    }