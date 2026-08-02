from flask import Flask, render_template, request, send_file
from datetime import datetime
import os
import csv
import json
import time

import pandas as pd
import faiss

from sentence_transformers import SentenceTransformer

# ===============================
# Milestone 2 Agents
# ===============================

from utils.triage_agent import triage_bug
from utils.log_analysis import analyze_log

# ===============================
# Milestone 3 Agents
# ===============================

try:
    from utils.root_cause_agent import root_cause_analysis
except:
    root_cause_analysis = None

try:
    from utils.duplicate_detection import find_duplicate_bugs
except:
    find_duplicate_bugs = None

try:
    from utils.remediation_agent import generate_remediation
except:
    generate_remediation = None

# ======================================================
# Flask App
# ======================================================

app = Flask(__name__)

# ======================================================
# Upload Folder
# ======================================================

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================================================
# JSON Analysis Folder
# ======================================================

ANALYSIS_FOLDER = "analysis_results"
os.makedirs(ANALYSIS_FOLDER, exist_ok=True)

# ======================================================
# Load AI Resources
# ======================================================

print("=" * 60)
print("Loading AI Smart Bug Analyzer...")
print("=" * 60)

print("Loading Sentence Transformer...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Loading Mozilla Dataset...")
bug_data = pd.read_csv(
    "dataset/mozilla/clean_mozilla.csv"
)

print("Loading FAISS Index...")
index = faiss.read_index(
    "dataset/mozilla/bug_index.faiss"
)

print("Resources Loaded Successfully")
print("=" * 60)
print("Sentence Transformer  : OK")
print("Mozilla Dataset       : OK")
print("FAISS Index           : OK")
print("Application Ready")
print("=" * 60)
# ============================================================
# AI Smart Fix Suggestion Engine
# ============================================================

def generate_fix_suggestion(bug_text, severity):

    bug = bug_text.lower()

    # =====================================================
    # Authentication Bugs
    # =====================================================

    if any(word in bug for word in [
        "login",
        "signin",
        "password",
        "authentication",
        "auth",
        "credential"
    ]):

        return {

            "category": "Authentication",

            "priority": "High",

            "root_cause": [
                "Authentication service failure.",
                "Invalid credentials.",
                "Session validation failed."
            ],

            "impact": [
                "Users cannot access the application.",
                "Authentication requests fail."
            ],

            "recommended_fix": [
                "Validate username and password.",
                "Check authentication service.",
                "Verify session configuration.",
                "Review user database records."
            ],

            "testing": [
                "Successful login test.",
                "Invalid login test.",
                "Session timeout validation."
            ],

            "prevention": [
                "Enable authentication logging.",
                "Use secure password validation.",
                "Monitor failed login attempts."
            ]
        }

    # =====================================================
    # Database Bugs
    # =====================================================

    elif any(word in bug for word in [
        "database",
        "mysql",
        "sql",
        "query",
        "oracle",
        "postgres"
    ]):

        return {

            "category": "Database",

            "priority": "High",

            "root_cause": [
                "Database connection failure.",
                "Invalid SQL query.",
                "Database record inconsistency."
            ],

            "impact": [
                "Unable to retrieve records.",
                "Application performance degraded."
            ],

            "recommended_fix": [
                "Verify database connectivity.",
                "Review SQL syntax.",
                "Check credentials.",
                "Restart database service."
            ],

            "testing": [
                "Connection testing.",
                "Execute SQL queries.",
                "Validate returned data."
            ],

            "prevention": [
                "Database health monitoring.",
                "Routine backup strategy.",
                "SQL optimization."
            ]
        }
        # =====================================================
    # API Bugs
    # =====================================================

    elif any(word in bug for word in [
        "api",
        "endpoint",
        "request",
        "response",
        "rest",
        "token"
    ]):

        return {

            "category": "API",

            "priority": "Medium",

            "root_cause": [
                "API endpoint unavailable.",
                "Invalid request parameters.",
                "Authentication token expired."
            ],

            "impact": [
                "External communication failed.",
                "Data synchronization interrupted."
            ],

            "recommended_fix": [
                "Verify endpoint URL.",
                "Validate request payload.",
                "Refresh authentication token.",
                "Handle timeout exceptions."
            ],

            "testing": [
                "API response validation.",
                "Status code verification.",
                "Timeout testing."
            ],

            "prevention": [
                "Retry mechanism.",
                "API monitoring.",
                "Rate-limit handling."
            ]
        }

    # =====================================================
    # File Upload Bugs
    # =====================================================

    elif any(word in bug for word in [
        "upload",
        "attachment",
        "image",
        "pdf",
        "file"
    ]):

        return {

            "category": "File Upload",

            "priority": "Medium",

            "root_cause": [
                "Unsupported file format.",
                "Upload directory unavailable.",
                "Maximum file size exceeded."
            ],

            "impact": [
                "Users cannot upload files.",
                "Business process interrupted."
            ],

            "recommended_fix": [
                "Validate upload folder.",
                "Verify file extensions.",
                "Increase upload size limit.",
                "Improve exception handling."
            ],

            "testing": [
                "Upload PDF.",
                "Upload Image.",
                "Upload invalid file."
            ],

            "prevention": [
                "Validate uploads.",
                "Restrict unsupported formats.",
                "Implement upload logging."
            ]
        }
        # =====================================================
    # Network Bugs
    # =====================================================

    elif any(word in bug for word in [
        "network",
        "connection",
        "timeout",
        "server",
        "internet",
        "socket"
    ]):

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
                "Requests fail unexpectedly."
            ],

            "recommended_fix": [
                "Verify network connectivity.",
                "Check server availability.",
                "Increase timeout values.",
                "Implement retry mechanism."
            ],

            "testing": [
                "Network connectivity testing.",
                "Server response testing.",
                "Timeout validation."
            ],

            "prevention": [
                "Continuous network monitoring.",
                "Automatic retry strategy.",
                "Server health checks."
            ]
        }

    # =====================================================
    # Null Reference Bugs
    # =====================================================

    elif any(word in bug for word in [
        "null",
        "none",
        "attributeerror",
        "nullpointer",
        "object reference"
    ]):

        return {

            "category": "Null Reference",

            "priority": "High",

            "root_cause": [
                "Object reference is None.",
                "Variable not initialized.",
                "Unexpected missing data."
            ],

            "impact": [
                "Application crash.",
                "Unexpected runtime exception."
            ],

            "recommended_fix": [
                "Check for None before access.",
                "Initialize all variables.",
                "Validate user input.",
                "Improve exception handling."
            ],

            "testing": [
                "Null value testing.",
                "Empty input testing.",
                "Exception handling validation."
            ],

            "prevention": [
                "Add null validation.",
                "Perform defensive programming.",
                "Improve input validation."
            ]
        }
        # =====================================================
    # Performance Bugs
    # =====================================================

    elif any(word in bug for word in [
        "slow",
        "performance",
        "memory",
        "cpu",
        "lag",
        "freeze"
    ]):

        return {

            "category": "Performance",

            "priority": "Medium",

            "root_cause": [
                "High memory consumption.",
                "Inefficient algorithm.",
                "Resource leak."
            ],

            "impact": [
                "Slow application response.",
                "Poor user experience."
            ],

            "recommended_fix": [
                "Optimize application logic.",
                "Release unused resources.",
                "Improve database queries.",
                "Profile application performance."
            ],

            "testing": [
                "Stress testing.",
                "Load testing.",
                "Memory profiling."
            ],

            "prevention": [
                "Performance monitoring.",
                "Algorithm optimization.",
                "Regular profiling."
            ]
        }

    # =====================================================
    # User Interface Bugs
    # =====================================================

    elif any(word in bug for word in [
        "button",
        "ui",
        "screen",
        "layout",
        "display",
        "css"
    ]):

        return {

            "category": "User Interface",

            "priority": "Low",

            "root_cause": [
                "Incorrect CSS styling.",
                "HTML rendering issue.",
                "Browser compatibility problem."
            ],

            "impact": [
                "Poor user experience.",
                "Improper page rendering."
            ],

            "recommended_fix": [
                "Verify HTML layout.",
                "Review CSS styling.",
                "Test responsive design.",
                "Validate browser compatibility."
            ],

            "testing": [
                "Desktop browser testing.",
                "Mobile responsiveness testing.",
                "Cross-browser validation."
            ],

            "prevention": [
                "Responsive UI design.",
                "UI regression testing.",
                "Cross-browser testing."
            ]
        }

    # =====================================================
    # Default Suggestion
    # =====================================================

    else:

        return {

            "category": "General Software Bug",

            "priority": "Medium",

            "root_cause": [
                "Unexpected application behavior.",
                "Software logic issue."
            ],

            "impact": [
                "Feature malfunction.",
                "Unexpected system response."
            ],

            "recommended_fix": [
                "Review application logs.",
                "Reproduce the issue.",
                "Identify the root cause.",
                "Apply code fixes.",
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

    # ---------------------------------------------
    # Start Analysis Timer
    # ---------------------------------------------

    start_time = time.time()

    # ---------------------------------------------
    # Get User Input
    # ---------------------------------------------

    bug_title = request.form["bug_title"]
    stack_trace = request.form.get("stack_trace", "")

    # Use the title as the bug report if the description field is removed
    bug_report = bug_title

    bug_file = request.files.get("bug_file")

    filename = ""

    filepath = ""

    # ---------------------------------------------
    # Input Validation
    # ---------------------------------------------

    if bug_title == "":
        return render_template(
            "index.html",
            error="Please enter Bug Title."
        )

    if bug_report == "" and (
        bug_file is None or bug_file.filename == ""
    ):
        return render_template(
            "index.html",
            error="Please enter Bug Description or upload a log file."
        )

    # ---------------------------------------------
    # Save Uploaded File
    # ---------------------------------------------

    if bug_file and bug_file.filename != "":

        filename = bug_file.filename

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        bug_file.save(filepath)

    # ---------------------------------------------
    # Run AI Triage Agent
    # ---------------------------------------------

    full_bug_report = f"""
Title:
{bug_title}

Stack Trace:
{stack_trace}
"""

    triage_result = triage_bug(full_bug_report)

    severity = triage_result["severity"]

    print("=" * 60)
    print("Triage Agent Completed")
    print("=" * 60)

    # ---------------------------------------------
    # Run Log Analysis
    # ---------------------------------------------

    if filename != "":

        with open(
            filepath,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            log_text = file.read()

        log_result = analyze_log(log_text)
        print("\nLOG RESULT")
        print(log_result)
        print("\n")

    else:

        log_result = {

            "issues": [

                {

                    "exception_type": "No Log Uploaded",

                    "failure_point": "-",

                    "line_number": "-",

                    "code_path": "-",

                    "error_message": "-",

                    "root_cause": "-",

                    "suggested_fix":
                        "Upload a log file to perform log analysis."

                }

            ]

        }

    print("=" * 60)
    print("Log Analysis Completed")
    print("=" * 60)
        # --------------------------------------------------------
    # Save Bug Report to CSV
    # --------------------------------------------------------

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
                "Bug Title",
                "Bug Report",
                "Stack Trace",
                "Uploaded File",
                "Submission Date"
            ])

        writer.writerow([
            bug_id,
            bug_title,
            bug_title,
            stack_trace,
            filename,
            submission_date
        ])

    print("=" * 60)
    print("Bug Report Saved")
    print("=" * 60)

    # --------------------------------------------------------
    # Generate Sentence Transformer Embedding
    # --------------------------------------------------------

    query_embedding = model.encode(
        [full_bug_report],
        convert_to_numpy=True
    ).astype("float32")

    # --------------------------------------------------------
    # FAISS Similarity Search
    # --------------------------------------------------------

    TOP_K = 3

    distances, indices = index.search(
        query_embedding,
        TOP_K
    )

    similar_bugs = []

    highest_similarity = 0

    confidence = "Low"

    for rank, idx in enumerate(indices[0]):

        similarity = round(
            (1 / (1 + distances[0][rank])) * 100,
            2
        )

        highest_similarity = max(
            highest_similarity,
            similarity
        )

        if similarity >= 95:
            confidence = "Very High"

        elif similarity >= 85:
            confidence = "High"

        elif similarity >= 70:
            confidence = "Medium"

        else:
            confidence = "Low"

        similar_bugs.append({

            "rank": rank + 1,

            "id": int(idx),

            "description":
                str(bug_data.iloc[idx]["Description"])[:350] + "...",

            "severity":
                str(bug_data.iloc[idx]["Severity"]),

            "similarity":
                similarity

        })

    print("=" * 60)
    print(f"Found {len(similar_bugs)} Similar Bugs")
    print("=" * 60)
        # --------------------------------------------------------
    # AI Smart Fix Advisor
    # --------------------------------------------------------

    ai_fix = generate_fix_suggestion(

        bug_report,

        similar_bugs[0]["severity"]

    )

    bug_category = ai_fix["category"]

    priority = ai_fix["priority"]

    # --------------------------------------------------------
    # Root Cause Agent (Milestone 3)
    # --------------------------------------------------------

    if root_cause_analysis:

        root_cause = root_cause_analysis(
            full_bug_report,
            similar_bugs,
            log_result
        )

    else:

        root_cause = {

            "root_cause":
                "Root Cause Agent not available.",

            "confidence": 0,

            "evidence": []

        }

    # --------------------------------------------------------
    # Duplicate Detection Agent (Milestone 3)
    # --------------------------------------------------------

    if find_duplicate_bugs:

        duplicate_results = find_duplicate_bugs(
            full_bug_report,
            similar_bugs
        )

    else:

        duplicate_results = similar_bugs

    # --------------------------------------------------------
    # Remediation Agent (Milestone 3)
    # --------------------------------------------------------

    if generate_remediation:

        remediation = generate_remediation(
            full_bug_report,
            root_cause,
            duplicate_results
        )

    else:

        remediation = {

            "summary":
                "Use AI Smart Fix Advisor recommendations.",

            "steps":
                ai_fix["recommended_fix"],

            "testing":
                ai_fix["testing"],

            "prevention":
                ai_fix["prevention"]

        }

    # --------------------------------------------------------
    # Analysis Time
    # --------------------------------------------------------

    analysis_time = round(

        time.time() - start_time,

        2

    )

    print("=" * 60)
    print(f"Analysis Completed in {analysis_time} seconds")
    print("=" * 60)
        # --------------------------------------------------------
    # Save JSON Report
    # --------------------------------------------------------

    combined_analysis = {

        "bug_id": bug_id,

        "submission_date": submission_date,

        "bug_title": bug_title,

        "bug_report": bug_report,

        "severity": severity,

        "uploaded_file": filename,

        "analysis_time": analysis_time,

        "triage": triage_result,

        "log_analysis": log_result,

        "similar_bugs": similar_bugs,

        "root_cause": root_cause,

        "duplicate_detection": duplicate_results,

        "remediation": remediation,

        "ai_fix": ai_fix

    }

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

    print("=" * 60)
    print("JSON Report Saved")
    print("=" * 60)

    # --------------------------------------------------------
    # Display Result
    # --------------------------------------------------------

    return render_template(

        "result.html",

        # Basic Information
        bug_id=bug_id,
        bug_title=bug_title,
        user_bug=bug_report,
        severity=severity,
        filename=filename,
        submission_date=submission_date,
        analysis_time=analysis_time,

        # Similar Bugs
        similar_bugs=similar_bugs,
        confidence=highest_similarity,

        # AI Smart Fix Advisor
        ai_fix=ai_fix,
        bug_category=bug_category,
        priority=priority,

        # Milestone 2
        triage=triage_result,
        log_analysis=log_result,

        # Milestone 3
        root_cause=root_cause,
        duplicate_detection=duplicate_results,
        remediation=remediation

    )


# ============================================================
# Health Check
# ============================================================

@app.route("/health")
def health():

    return {

        "status": "running",

        "project": "AI Smart Bug Analyzer",

        "version": "3.0",

        "milestone": "Milestone 3",

        "agents": [

            "Triage Agent",

            "Log Analysis Agent",

            "Root Cause Agent",

            "Duplicate Detection Agent",

            "Remediation Agent"

        ]

    }
@app.route("/download/<int:bug_id>")
def download_report(bug_id):

    json_filename = f"bug_{bug_id}.json"
    json_path = os.path.join(ANALYSIS_FOLDER, json_filename)

    if os.path.exists(json_path):
        return send_file(
            json_path,
            as_attachment=True,
            download_name=json_filename,
            mimetype="application/json"
        )

    return "JSON report not found.", 404


# ============================================================
# Run Flask Application
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000

    )