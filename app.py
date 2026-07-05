from flask import Flask, render_template, request
from datetime import datetime
import os
import csv
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

app = Flask(__name__)

# -----------------------------
# Upload Folder
# -----------------------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Configure Gemini AI
# -------------------------
genai.configure(api_key="YOUR_API_KEY")

gemini = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# Load AI Model
# -----------------------------
print("Loading AI Model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

bug_data = pd.read_csv("dataset/mozilla/clean_mozilla.csv")

index = faiss.read_index("dataset/mozilla/bug_index.faiss")

print("AI Ready!")

# -----------------------------
# Home Page
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Submit Bug
# -----------------------------
@app.route("/submit", methods=["POST"])
def submit():

    bug_report = request.form["bug_report"]
    bug_file = request.files["bug_file"]

    filename = ""

    # -----------------------------
    # Save Uploaded File
    # -----------------------------
    if bug_file.filename != "":
        filename = bug_file.filename
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        bug_file.save(filepath)

    # -----------------------------
    # Save Bug Report to CSV
    # -----------------------------
    csv_file = "bug_reports.csv"

    file_exists = os.path.isfile(csv_file)

    bug_id = 1

    if file_exists:
        with open(csv_file, "r", encoding="utf-8") as file:
            bug_id = max(sum(1 for _ in file), 1)

    submission_date = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    with open(csv_file, "a", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        if not file_exists or os.path.getsize(csv_file) == 0:
            writer.writerow([
                "Bug ID",
                "Bug Report",
                "Uploaded File",
                "Submission Date"
            ])

        writer.writerow([
            bug_id,
            bug_report,
            filename,
            submission_date
        ])

    # -----------------------------
    # AI Similarity Search
    # -----------------------------
    query_embedding = model.encode(
        [bug_report],
        convert_to_numpy=True
    ).astype("float32")

    distances, indices = index.search(query_embedding, 5)

    similar_bugs = []

    for rank, i in enumerate(indices[0]):

        similarity = round(
            (1 / (1 + distances[0][rank])) * 100,
            2
        )

        similar_bugs.append({

            "description": bug_data.iloc[i]["Description"][:350] + "...",

            "severity": bug_data.iloc[i]["Severity"],

            "score": similarity

        })

    # -----------------------------
    # Gemini AI Fix Suggestion
    # -----------------------------
    prompt = f"""
You are an experienced Software Debugging Expert.

User Bug Report:
{bug_report}

Most Similar Bug:
{similar_bugs[0]["description"]}

Severity:
{similar_bugs[0]["severity"]}

Give the answer in plain text.

Format:

Possible Cause
- point
- point

Recommended Fix
- point
- point

Prevention Tips
- point
- point

Do NOT use markdown.
Keep the answer short and professional.
"""

    try:

        response = gemini.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            ai_fix = response.text
        else:
            ai_fix = "AI could not generate a suggestion."

    except Exception as e:

        ai_fix = f"Gemini Error: {str(e)}"

    # -----------------------------
    # Show Result Page
    # -----------------------------
    return render_template(

        "result.html",

        user_bug=bug_report,

        similar_bugs=similar_bugs,

        ai_fix=ai_fix,

        filename=filename,

        submission_date=submission_date,

        bug_id=bug_id

    )


# -----------------------------
# Run Flask
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)