import os
import re
import numpy as np
import pandas as pd
import faiss

from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATASET_FOLDER = os.path.join(
    BASE_DIR,
    "dataset"
)

MOZILLA_CSV = os.path.join(
    DATASET_FOLDER,
    "mozilla",
    "clean_mozilla.csv"
)

MOZILLA_INDEX = os.path.join(
    DATASET_FOLDER,
    "mozilla",
    "bug_index.faiss"
)

VERIFIED_BUGS_FILE = os.path.join(
    DATASET_FOLDER,
    "growth_knowledge_base",
    "verified_bugs.json"
)

VERIFIED_INDEX = os.path.join(
    DATASET_FOLDER,
    "growth_knowledge_base",
    "verified_bugs.faiss"
)


_model = None
_mozilla_df = None
_mozilla_index = None
_verified_index = None
_verified_bugs = []


def clean_text(value):
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def load_model():

    global _model

    if _model is None:

        _model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    return _model


def load_mozilla():

    global _mozilla_df
    global _mozilla_index

    if _mozilla_df is None:

        if not os.path.exists(
            MOZILLA_CSV
        ):
            return None, None

        _mozilla_df = pd.read_csv(
            MOZILLA_CSV
        )

    if _mozilla_index is None:

        if os.path.exists(
            MOZILLA_INDEX
        ):

            _mozilla_index = (
                faiss.read_index(
                    MOZILLA_INDEX
                )
            )

    return (
        _mozilla_df,
        _mozilla_index
    )


def load_verified():

    global _verified_bugs
    global _verified_index

    if os.path.exists(
        VERIFIED_BUGS_FILE
    ):

        try:

            import json

            with open(
                VERIFIED_BUGS_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                _verified_bugs = json.load(f)

        except Exception:

            _verified_bugs = []

    else:

        _verified_bugs = []

    if os.path.exists(
        VERIFIED_INDEX
    ):

        try:

            _verified_index = (
                faiss.read_index(
                    VERIFIED_INDEX
                )
            )

        except Exception:

            _verified_index = None

    return (
        _verified_bugs,
        _verified_index
    )


def semantic_search(
    text,
    top_k=5
):

    text = clean_text(text)

    if not text:
        return []

    model = load_model()

    query_vector = model.encode(
        [text],
        convert_to_numpy=True
    ).astype("float32")

    results = []

    # --------------------------------------------------
    # Mozilla knowledge base
    # --------------------------------------------------

    df, index = load_mozilla()

    if (
        df is not None
        and index is not None
        and len(df) > 0
    ):

        distances, indices = (
            index.search(
                query_vector,
                top_k
            )
        )

        for rank, idx in enumerate(
            indices[0]
        ):

            if idx < 0:
                continue

            if idx >= len(df):
                continue

            row = df.iloc[
                int(idx)
            ]

            distance = float(
                distances[0][rank]
            )

            similarity = (
                100.0 /
                (1.0 + max(distance, 0.0))
            )

            description = clean_text(
                row.get(
                    "Description",
                    row.get(
                        "description",
                        ""
                    )
                )
            )

            title = clean_text(
                row.get(
                    "Summary",
                    row.get(
                        "Title",
                        "Historical Bug"
                    )
                )
            )

            results.append({

                "source":
                    "Mozilla",

                "bug_id":
                    row.get(
                        "Bug ID",
                        row.get(
                            "id",
                            rank + 1
                        )
                    ),

                "title":
                    title,

                "description":
                    description,

                "severity":
                    clean_text(
                        row.get(
                            "Severity",
                            "Unknown"
                        )
                    ),

                "priority":
                    clean_text(
                        row.get(
                            "Priority",
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

                "root_cause":
                    clean_text(
                        row.get(
                            "Root Cause",
                            ""
                        )
                    ),

                "resolution":
                    clean_text(
                        row.get(
                            "Resolution",
                            ""
                        )
                    ),

                "similarity":
                    round(
                        similarity,
                        2
                    )
            })

    # --------------------------------------------------
    # Verified growth knowledge base
    # --------------------------------------------------

    verified, verified_index = (
        load_verified()
    )

    if (
        verified_index is not None
        and verified
    ):

        count = min(
            top_k,
            verified_index.ntotal
        )

        if count > 0:

            distances, indices = (
                verified_index.search(
                    query_vector,
                    count
                )
            )

            for rank, idx in enumerate(
                indices[0]
            ):

                if idx < 0:
                    continue

                if idx >= len(verified):
                    continue

                item = verified[
                    int(idx)
                ]

                distance = float(
                    distances[0][rank]
                )

                similarity = (
                    100.0 /
                    (
                        1.0 +
                        max(
                            distance,
                            0.0
                        )
                    )
                )

                results.append({

                    "source":
                        "Verified",

                    "bug_id":
                        item.get(
                            "bug_id",
                            "Unknown"
                        ),

                    "title":
                        clean_text(
                            item.get(
                                "bug_title",
                                "Verified Bug"
                            )
                        ),

                    "description":
                        clean_text(
                            item.get(
                                "bug_report",
                                ""
                            )
                        ),

                    "severity":
                        clean_text(
                            item.get(
                                "severity",
                                "Unknown"
                            )
                        ),

                    "priority":
                        clean_text(
                            item.get(
                                "priority",
                                "Unknown"
                            )
                        ),

                    "component":
                        clean_text(
                            item.get(
                                "component",
                                "Unknown"
                            )
                        ),

                    "root_cause":
                        clean_text(
                            item.get(
                                "root_cause",
                                ""
                            )
                        ),

                    "resolution":
                        clean_text(
                            item.get(
                                "resolution",
                                ""
                            )
                        ),

                    "similarity":
                        round(
                            similarity,
                            2
                        )
                })

    # --------------------------------------------------
    # Remove duplicates and rank
    # --------------------------------------------------

    unique = {}

    for item in results:

        key = str(
            item.get(
                "bug_id"
            )
        )

        if (
            key not in unique
            or
            item["similarity"]
            >
            unique[key]["similarity"]
        ):

            unique[key] = item

    results = list(
        unique.values()
    )

    results.sort(
        key=lambda x:
            float(
                x.get(
                    "similarity",
                    0
                )
            ),
        reverse=True
    )

    return results[:top_k]