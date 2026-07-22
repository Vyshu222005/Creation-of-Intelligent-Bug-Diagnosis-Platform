from flask import Flask, render_template, request
from datetime import datetime
import os
import csv
import json
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# ===============================
# Milestone 2 Agents
# ===============================
from utils.triage_agent import triage_bug
from utils.log_analysis import analyze_log

app = Flask(__name__)

# ============================================================
# Upload Folder Configuration
# ============================================================

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
# Analysis Results Folder
# ============================================================

ANALYSIS_FOLDER = "analysis_results"
os.makedirs(ANALYSIS_FOLDER, exist_ok=True)

# ============================================================
# Load AI Model
# ============================================================

print("=" * 60)
print("Loading AI Smart Bug Analyzer...")
print("=" * 60)

model = SentenceTransformer("all-MiniLM-L6-v2")

bug_data = pd.read_csv(
    "dataset/mozilla/clean_mozilla.csv"
)

index = faiss.read_index(
    "dataset/mozilla/bug_index.faiss"
)

print("Sentence Transformer Loaded Successfully")
print("FAISS Index Loaded Successfully")
print("Mozilla Dataset Loaded Successfully")
print("AI Smart Bug Analyzer Ready!")
print("=" * 60)

# ============================================================
# Offline Intelligent Fix Suggestion Engine
# ============================================================

def generate_fix_suggestion(bug_text, severity):

    bug = bug_text.lower()

    # ------------------------------------
    # Authentication Bugs
    # ------------------------------------

    if any(word in bug for word in
           ["login", "password", "authentication", "signin"]):

        return {

            "category": "Authentication",

            "priority": "High",

            "root_cause": [

                "Authentication service failure.",

                "Invalid username or password.",

                "Session validation failed."

            ],

            "impact": [

                "User cannot access the system.",

                "Application functionality interrupted."

            ],

            "recommended_fix": [

                "Verify username and password.",

                "Validate authentication module.",

                "Check session handling.",

                "Verify user database records."

            ],

            "testing": [

                "Test valid login.",

                "Test invalid login.",

                "Verify session timeout."

            ],

            "prevention": [

                "Enable authentication logging.",

                "Use secure password validation.",

                "Monitor failed login attempts."

            ]

        }

    # ------------------------------------
    # Database Bugs
    # ------------------------------------

    elif any(word in bug for word in
             ["database", "sql", "mysql", "query"]):

        return {

            "category": "Database",

            "priority": "High",

            "root_cause": [

                "Database connection failure.",

                "Invalid SQL query.",

                "Missing records."

            ],

            "impact": [

                "Unable to retrieve data.",

                "Application response delayed."

            ],

            "recommended_fix": [

                "Verify database connection.",

                "Check SQL syntax.",

                "Validate credentials.",

                "Restart database service."

            ],

            "testing": [

                "Test database connection.",

                "Execute SQL queries.",

                "Validate returned records."

            ],

            "prevention": [

                "Monitor database health.",

                "Perform regular backups.",

                "Optimize SQL queries."

            ]

        }
        # ------------------------------------
    # API Bugs
    # ------------------------------------

    elif any(word in bug for word in
             ["api", "endpoint", "request", "response"]):

        return {

            "category": "API",

            "priority": "Medium",

            "root_cause": [

                "API communication failed.",

                "Invalid request.",

                "Authentication token expired."

            ],

            "impact": [

                "External service unavailable.",

                "Data synchronization failed."

            ],

            "recommended_fix": [

                "Verify API endpoint.",

                "Check request parameters.",

                "Refresh authentication token.",

                "Handle timeout exceptions."

            ],

            "testing": [

                "Test API response.",

                "Validate status codes.",

                "Verify timeout handling."

            ],

            "prevention": [

                "Implement retry mechanism.",

                "Monitor API performance."

            ]

        }

    # ------------------------------------
    # File Upload Bugs
    # ------------------------------------

    elif any(word in bug for word in
             ["upload", "file", "pdf", "image", "attachment"]):

        return {

            "category": "File Upload",

            "priority": "Medium",

            "root_cause": [

                "Invalid file format.",

                "Upload directory not found.",

                "File size exceeded."

            ],

            "impact": [

                "User cannot upload files.",

                "Required documents unavailable."

            ],

            "recommended_fix": [

                "Verify upload folder exists.",

                "Validate file extension.",

                "Increase upload size limit if required.",

                "Handle upload exceptions."

            ],

            "testing": [

                "Upload PDF.",

                "Upload Image.",

                "Upload Invalid File."

            ],

            "prevention": [

                "Restrict unsupported formats.",

                "Validate uploaded files."

            ]

        }

    # ------------------------------------
    # Network Bugs
    # ------------------------------------

    elif any(word in bug for word in
             ["network", "connection", "timeout", "internet", "server"]):

        return {

            "category": "Network",

            "priority": "Medium",

            "root_cause": [

                "Network interruption.",

                "Server unavailable.",

                "Connection timeout."

            ],

            "impact": [

                "Application cannot communicate with server.",

                "Request failed."

            ],

            "recommended_fix": [

                "Check internet connection.",

                "Verify server availability.",

                "Increase timeout value.",

                "Retry failed requests."

            ],

            "testing": [

                "Test internet connectivity.",

                "Ping server.",

                "Verify timeout handling."

            ],

            "prevention": [

                "Monitor network.",

                "Implement retry mechanism."

            ]

        }
        # ------------------------------------
    # Null Reference Bugs
    # ------------------------------------

    elif any(word in bug for word in
             ["null", "none", "attributeerror", "nullpointer"]):

        return {

            "category": "Null Reference",

            "priority": "High",

            "root_cause": [

                "Object is None.",

                "Variable not initialized.",

                "Missing data."

            ],

            "impact": [

                "Application crash.",

                "Unexpected exception."

            ],

            "recommended_fix": [

                "Check for None before accessing object.",

                "Initialize variables.",

                "Validate user input.",

                "Use exception handling."

            ],

            "testing": [

                "Test null values.",

                "Validate empty inputs.",

                "Run exception tests."

            ],

            "prevention": [

                "Perform null checking.",

                "Improve validation."

            ]

        }

    # ------------------------------------
    # Performance Bugs
    # ------------------------------------

    elif any(word in bug for word in
             ["slow", "performance", "memory", "cpu", "lag"]):

        return {

            "category": "Performance",

            "priority": "Medium",

            "root_cause": [

                "High memory usage.",

                "Inefficient algorithm.",

                "Resource leak."

            ],

            "impact": [

                "Application becomes slow.",

                "Poor user experience."

            ],

            "recommended_fix": [

                "Optimize code.",

                "Release unused memory.",

                "Improve database queries.",

                "Profile application."

            ],

            "testing": [

                "Stress testing.",

                "Performance testing.",

                "Memory usage monitoring."

            ],

            "prevention": [

                "Optimize algorithms.",

                "Monitor CPU and RAM."

            ]

        }

    # ------------------------------------
    # UI Bugs
    # ------------------------------------

    elif any(word in bug for word in
             ["button", "ui", "screen", "layout", "display", "css"]):

        return {

            "category": "User Interface",

            "priority": "Low",

            "root_cause": [

                "Incorrect CSS styling.",

                "HTML rendering issue.",

                "Browser compatibility."

            ],

            "impact": [

                "Poor user experience.",

                "Incorrect page display."

            ],

            "recommended_fix": [

                "Verify HTML layout.",

                "Check CSS styles.",

                "Test responsive design.",

                "Verify browser compatibility."

            ],

            "testing": [

                "Desktop testing.",

                "Mobile testing.",

                "Cross-browser testing."

            ],

            "prevention": [

                "Responsive design.",

                "UI testing."

            ]

        }
        # ------------------------------------
    # Default AI Suggestion
    # ------------------------------------

    else:

        return {

            "category": "General Software Bug",

            "priority": "Medium",

            "root_cause": [

                "Unexpected application behavior.",

                "Software logic issue."

            ],

            "impact": [

                "Feature not working correctly.",

                "Unexpected system response."

            ],

            "recommended_fix": [

                "Review application logs.",

                "Reproduce the issue.",

                "Identify root cause.",

                "Apply required code changes.",

                "Perform regression testing."

            ],

            "testing": [

                "Functional testing.",

                "Regression testing.",

                "Integration testing."

            ],

            "prevention": [

                "Regular code reviews.",

                "Improve logging.",

                "Continuous testing."

            ]

        }


# ============================================================
# Home Page
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# Submit Bug
# ============================================================

@app.route("/submit", methods=["POST"])
def submit():

    # --------------------------------------------------------
    # Get User Input
    # --------------------------------------------------------

    bug_report = request.form["bug_report"]

    bug_file = request.files["bug_file"]
    bug_title = request.form.get("bug_title")
    severity = request.form.get("severity")
    bug_report = request.form.get("bug_report")

    filename = ""

    # --------------------------------------------------------
    # Milestone 2
    # Run Triage Agent
    # --------------------------------------------------------

    triage_result = triage_bug(bug_report)

    # --------------------------------------------------------
    # Milestone 2
    # Run Log Analysis Agent
    # --------------------------------------------------------

    log_result = analyze_log(bug_report)

    # --------------------------------------------------------
    # Validate User Input
    # --------------------------------------------------------

    bug_report = bug_report.strip()

    if bug_report == "" and bug_file.filename == "":

        return render_template(

            "index.html",

            error="Please enter a bug description or upload a bug report."

        )

    # --------------------------------------------------------
    # Save Uploaded File
    # --------------------------------------------------------

    if bug_file.filename != "":

        filename = bug_file.filename

        filepath = os.path.join(

            app.config["UPLOAD_FOLDER"],

            filename

        )

        bug_file.save(filepath)

    # --------------------------------------------------------
    # Save Bug Report to CSV
    # --------------------------------------------------------

    csv_file = "bug_reports.csv"

    file_exists = os.path.isfile(csv_file)

    bug_id = 1

    if file_exists:

        with open(

            csv_file,

            "r",

            encoding="utf-8"

        ) as file:

            bug_id = max(sum(1 for _ in file), 1)

    submission_date = datetime.now().strftime(

        "%d-%m-%Y %I:%M %p"

    )

    with open(

        csv_file,

        "a",

        newline="",

        encoding="utf-8"

    ) as file:

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
            # --------------------------------------------------------
    # Generate Embedding
    # --------------------------------------------------------

    query_embedding = model.encode(

        [bug_report],

        convert_to_numpy=True

    ).astype("float32")

    # --------------------------------------------------------
    # FAISS Search
    # --------------------------------------------------------

    distances, indices = index.search(

        query_embedding,

        3

    )

    similar_bugs = []

    confidence = "Low"

    for rank, i in enumerate(indices[0]):

        similarity = round(

            (1 / (1 + distances[0][rank])) * 100,

            2

        )

        if similarity >= 90:

            confidence = "Very High"

        elif similarity >= 80:

            confidence = "High"

        elif similarity >= 70:

            confidence = "Medium"

        else:

            confidence = "Low"

        similar_bugs.append({

            "description":

            bug_data.iloc[i]["Description"][:350] + "...",

            "severity":

            bug_data.iloc[i]["Severity"],

            "score":

            similarity

        })

    # --------------------------------------------------------
    # Generate Offline AI Fix
    # --------------------------------------------------------

    ai_fix = generate_fix_suggestion(

        bug_report,

        similar_bugs[0]["severity"]

    )

    bug_category = ai_fix["category"]

    priority = ai_fix["priority"]

    # ============================================================
    # Milestone 2
    # Combine Triage + Log Analysis + RAG Results
    # ============================================================

    combined_analysis = {

        "bug_id": bug_id,

        "submission_date": submission_date,

        "bug_report": bug_report,

        "uploaded_file": filename,

        "triage": triage_result,

        "log_analysis": log_result,

        "similar_bugs": similar_bugs,

        "ai_fix": ai_fix

    }

    # ============================================================
    # Save Analysis as JSON
    # ============================================================

    json_filename = f"bug_{bug_id}.json"

    json_path = os.path.join(

        ANALYSIS_FOLDER,

        json_filename

    )

    with open(

        json_path,

        "w",

        encoding="utf-8"

    ) as json_file:

        json.dump(

            combined_analysis,

            json_file,

            indent=4

        )
            # ============================================================
    # Display Result Page
    # ============================================================

    return render_template(

        "result.html",

        # -----------------------------
        # User Details
        # -----------------------------

        user_bug=bug_report,

        filename=filename,

        submission_date=submission_date,

        bug_id=bug_id,

        # -----------------------------
        # RAG Results
        # -----------------------------

        similar_bugs=similar_bugs,

        confidence=confidence,

        # -----------------------------
        # AI Fix Suggestion
        # -----------------------------

        ai_fix=ai_fix,

        bug_category=bug_category,

        priority=priority,

        # -----------------------------
        # Milestone 2
        # Triage Agent Output
        # -----------------------------

        triage=triage_result,

        # -----------------------------
        # Milestone 2
        # Log Analysis Output
        # -----------------------------

        log_analysis=log_result

    )


# ============================================================
# Health Check (Optional)
# ============================================================

@app.route("/health")
def health():

    return {

        "status": "running",

        "project": "AI Smart Bug Analyzer",

        "milestone": "Milestone 2",

        "agents": [

            "Triage Agent",

            "Log Analysis Agent"

        ]

    }


# ============================================================
# Run Flask Application
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000

    )