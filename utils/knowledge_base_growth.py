import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

KB_FOLDER = "dataset/growth_knowledge_base"

KB_JSON = os.path.join(
    KB_FOLDER,
    "verified_bugs.json"
)

KB_INDEX = os.path.join(
    KB_FOLDER,
    "verified_bugs.faiss"
)

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# Create Folder
# ============================================================

os.makedirs(
    KB_FOLDER,
    exist_ok=True
)


# ============================================================
# Load Sentence Transformer
# ============================================================

model = SentenceTransformer(
    MODEL_NAME
)


# ============================================================
# Load Verified Bugs
# ============================================================

def load_verified_bugs():

    if not os.path.exists(KB_JSON):

        return []

    try:

        with open(
            KB_JSON,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):

            return data

    except Exception as e:

        print(
            "Error loading verified bugs:",
            e
        )

    return []


# ============================================================
# Save Verified Bugs
# ============================================================

def save_verified_bugs(bugs):

    with open(
        KB_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            bugs,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# Create Text for Embedding
# ============================================================

def create_bug_text(bug):

    return f"""
Bug Title:
{bug.get("bug_title", "")}

Bug Description:
{bug.get("bug_report", "")}

Severity:
{bug.get("severity", "")}

Root Cause:
{bug.get("root_cause", "")}

Resolution:
{bug.get("resolution", "")}

Component:
{bug.get("component", "")}
""".strip()


# ============================================================
# Rebuild FAISS Index
# ============================================================

def rebuild_index():

    bugs = load_verified_bugs()

    if not bugs:

        print(
            "No verified bugs available."
        )

        return False

    texts = [
        create_bug_text(bug)
        for bug in bugs
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True
    ).astype("float32")

    # Normalize embeddings
    faiss.normalize_L2(
        embeddings
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(
        embeddings
    )

    faiss.write_index(
        index,
        KB_INDEX
    )

    print(
        "=" * 60
    )

    print(
        "Knowledge Base Index Updated"
    )

    print(
        f"Verified Bugs: {len(bugs)}"
    )

    print(
        f"FAISS Vectors: {index.ntotal}"
    )

    print(
        "=" * 60
    )

    return True


# ============================================================
# Add Verified Bug
# ============================================================

def add_verified_bug(
    bug_id,
    bug_title,
    bug_report,
    severity,
    root_cause,
    resolution,
    component="Unknown"
):

    bugs = load_verified_bugs()

    # Prevent duplicate bug IDs
    for bug in bugs:

        if str(
            bug.get("bug_id")
        ) == str(bug_id):

            return {
                "success": False,
                "message":
                    "This bug is already in the knowledge base."
            }

    new_bug = {

        "bug_id":
            str(bug_id),

        "bug_title":
            bug_title,

        "bug_report":
            bug_report,

        "severity":
            severity,

        "root_cause":
            root_cause,

        "resolution":
            resolution,

        "component":
            component,

        "verified":
            True
    }

    bugs.append(
        new_bug
    )

    save_verified_bugs(
        bugs
    )

    success = rebuild_index()

    if success:

        return {
            "success": True,
            "message":
                "Verified bug added to knowledge base successfully.",
            "bug_id":
                str(bug_id),
            "total_verified_bugs":
                len(bugs)
        }

    return {
        "success": False,
        "message":
            "Bug saved, but FAISS index could not be updated."
    }


# ============================================================
# Search Growth Knowledge Base
# ============================================================

def search_verified_bugs(
    query,
    top_k=5
):

    if not os.path.exists(KB_INDEX):

        return []

    bugs = load_verified_bugs()

    if not bugs:

        return []

    index = faiss.read_index(
        KB_INDEX
    )

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    faiss.normalize_L2(
        query_embedding
    )

    k = min(
        top_k,
        len(bugs)
    )

    scores, indices = index.search(
        query_embedding,
        k
    )

    results = []

    for rank, idx in enumerate(
        indices[0]
    ):

        if idx < 0:
            continue

        if idx >= len(bugs):
            continue

        bug = bugs[idx]

        results.append({

            "rank":
                rank + 1,

            "bug_id":
                bug.get("bug_id"),

            "title":
                bug.get("bug_title"),

            "description":
                bug.get("bug_report"),

            "root_cause":
                bug.get("root_cause"),

            "resolution":
                bug.get("resolution"),

            "component":
                bug.get("component"),

            "similarity":
                round(
                    float(
                        scores[0][rank]
                    ) * 100,
                    2
                )
        })

    return results