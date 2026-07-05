import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

print("Loading cleaned dataset...")

# Read cleaned dataset
data = pd.read_csv("dataset/mozilla/clean_mozilla.csv")

# Use only first 1000 bug reports for Milestone 1
data = data.head(1000)

# Get bug descriptions
descriptions = data["Description"].astype(str).tolist()

print("Loading embedding model...")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Generating embeddings...")

# Convert descriptions into embeddings
embeddings = model.encode(
    descriptions,
    show_progress_bar=True,
    convert_to_numpy=True
)

# Convert to float32 (required by FAISS)
embeddings = embeddings.astype("float32")

print("Creating FAISS index...")

# Create FAISS vector database
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)

# Add vectors
index.add(embeddings)

# Save vector database
faiss.write_index(index, "dataset/mozilla/bug_index.faiss")

print("====================================")
print("Vector Database Created Successfully!")
print("Total Bug Reports Indexed:", index.ntotal)
print("====================================")