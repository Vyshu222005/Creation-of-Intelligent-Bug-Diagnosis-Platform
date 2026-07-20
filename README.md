# 🤖 AI Smart Bug Analyzer & Intelligent Fix Advisor

## 📌 Project Overview

AI Smart Bug Analyzer & Intelligent Fix Advisor is an intelligent web application developed using Flask and Artificial Intelligence techniques to automate bug analysis. The system accepts bug reports, retrieves similar historical bugs using a Retrieval-Augmented Generation (RAG) approach, classifies the bug using AI agents, analyzes stack traces, and provides intelligent fix recommendations.

This project was developed as part of the **Infosys Springboard Internship - Milestone 2**.

---

# 🎯 Objectives

- Automate software bug analysis.
- Reduce manual bug triaging effort.
- Retrieve similar historical bugs.
- Classify bug severity and priority.
- Analyze stack traces and log files.
- Suggest intelligent fixes based on bug type.
- Generate structured analysis reports.

---

# 🚀 Features

## ✅ Bug Submission Module

- Submit bug descriptions.
- Upload bug report files.
- Store bug reports in CSV.

---

## ✅ Historical Bug Retrieval (RAG)

- Mozilla Bug Dataset
- Sentence Transformers
- FAISS Vector Search
- Top similar bug retrieval

---

## ✅ AI Smart Fix Advisor

Provides:

- Bug Category
- Priority
- Root Cause Analysis
- Impact Analysis
- Recommended Fixes
- Testing Recommendations
- Prevention Tips

---

## ✅ Triage Agent (Milestone 2)

Automatically predicts:

- Severity
- Priority
- Affected Component
- Confidence Score
- Reasoning

---

## ✅ Log Analysis Agent (Milestone 2)

Analyzes stack traces and error logs.

Extracts:

- Exception Type
- Failure Point
- Line Number
- Code Path
- Error Message

---

## ✅ Multi-Agent Orchestration (Milestone 2)

After bug submission:

1. Bug is submitted.
2. Triage Agent analyzes the bug.
3. Log Analysis Agent parses logs.
4. Historical bugs are retrieved.
5. AI Fix Advisor generates recommendations.
6. JSON analysis report is generated.

---

# 🛠 Technology Stack

## Frontend

- HTML5
- CSS3

## Backend

- Python
- Flask

## AI / ML

- Sentence Transformers
- FAISS

## Dataset

- Mozilla Bug Dataset

## Storage

- CSV
- JSON

---

# 📂 Project Structure

```text
AI-SMART-BUG-ANALYZER/

│── app.py
│── preprocess.py
│── build_vector_db.py
│── search_bug.py
│── requirements.txt
│── README.md
│── bug_reports.csv

│
├── dataset/
│   └── mozilla/
│       ├── clean_mozilla.csv
│       ├── mozilla_bugs.csv
│       └── bug_index.faiss
│
├── templates/
│   ├── index.html
│   └── result.html
│
├── static/
│
├── uploads/
│
├── analysis_results/
│
└── utils/
    ├── triage_agent.py
    └── log_analysis.py
```

---

# 🔄 Workflow

```text
User
   │
   ▼
Bug Submission
   │
   ▼
Triage Agent
   │
   ▼
Log Analysis Agent
   │
   ▼
FAISS Similar Bug Retrieval
   │
   ▼
AI Smart Fix Advisor
   │
   ▼
JSON Report Generation
   │
   ▼
Result Dashboard
```

---

# 📊 Outputs

The application generates:

- Bug Analysis Summary
- Submitted Bug Report
- Triage Agent Results
- Log Analysis Results
- Similar Historical Bugs
- AI Smart Fix Recommendations
- JSON Analysis Report

---

# 📁 JSON Output

Every bug analysis is stored inside:

```
analysis_results/
```

Example:

```
bug_1.json
bug_2.json
bug_3.json
```

---

# ▶️ Installation

Clone the repository

```bash
git clone <repository_url>
```

Move into project folder

```bash
cd AI-SMART-BUG-ANALYZER
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python app.py
```

Open browser

```
http://127.0.0.1:5000
```

---

# 📸 Application Modules

- Home Page
- Bug Submission
- Bug Analysis Summary
- Triage Agent
- Log Analysis Agent
- Similar Historical Bugs
- AI Smart Fix Advisor

---

# 🎯 Milestone 2 Deliverables Completed

✅ Triage Agent

✅ Log Analysis Agent

✅ Multi-Agent Orchestration

✅ Structured JSON Output

---

# 👩‍💻 Developed By

**Vyshnavi Polavarapu**

B.Tech CSE (AI & ML)

Narayana Engineering College, Nellore

---

# 📜 Internship

**Infosys Springboard Internship**

**Milestone 2 Project**