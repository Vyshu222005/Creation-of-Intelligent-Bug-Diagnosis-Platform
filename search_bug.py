import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

print("Loading vector database...")

# Load dataset
data = pd.read_csv("dataset/mozilla/clean_mozilla.csv")

# Load FAISS index
index = faiss.read_index("dataset/mozilla/bug_index.faiss")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Ready!")

while True:

    query = input("\nEnter Bug Report: ")

    if query.lower() == "exit":
        break

    # Convert query to embedding
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    # Search top 5 similar bugs
    distances, indices = index.search(query_embedding, 5)

    print("\nTop Similar Bugs:\n")

    for i in indices[0]:
        print("--------------------------------------")
        print(data.iloc[i]["Description"])

        if "Severity" in data.columns:
            print("Severity:", data.iloc[i]["Severity"])

        print("--------------------------------------")