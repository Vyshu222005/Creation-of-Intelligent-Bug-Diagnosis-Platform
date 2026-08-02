# 🤖 AI Smart Bug Analyzer & Fix Advisor

An AI-powered Software Defect Analysis platform that automatically analyzes bug reports, identifies root causes, detects duplicate bugs, performs log analysis, and generates intelligent remediation recommendations using Large Language Models (Ollama Llama 3.2), Retrieval-Augmented Generation (RAG), and FAISS vector search.

---

## 📌 Project Overview

AI Smart Bug Analyzer & Fix Advisor is an intelligent bug analysis system that assists software developers in diagnosing and resolving software defects.

The platform combines multiple AI agents to analyze uploaded bug reports and log files, retrieve historical defects, identify similar issues, determine the probable root cause, and recommend actionable fixes.

---

# 🚀 Milestone 3 Features

## ✅ AI Triage Agent
- Predicts Bug Severity
- Assigns Priority Level
- Detects Affected Component
- Generates AI Reasoning
- Confidence Score

---

## ✅ Log Analysis Agent

Automatically extracts:

- Exception Type
- Failure Point
- Line Number
- Code Path
- Error Message
- Root Cause
- Suggested Fix

---

## ✅ Root Cause Agent

Uses Retrieval-Augmented Generation (RAG) with historical defect knowledge to identify:

- Root Cause Hypothesis
- Confidence Score
- Supporting Historical Evidence

---

## ✅ Duplicate Detection Agent

Performs semantic similarity search using FAISS.

Displays:

- Top Matching Historical Bugs
- Similarity Score
- Historical Resolution Summary

---

## ✅ Remediation Agent

Generates intelligent recommendations including:

- Remediation Summary
- Recommended Fixes
- Testing Strategy
- Prevention Strategy

---

## ✅ Analytics Dashboard

Provides interactive visualizations:

- AI Confidence Chart
- Severity Analysis Chart

---

## ✅ Reports

Supports:

- Download JSON Report
- Print Report
- Analyze Another Bug

---

# 🧠 AI Technologies Used

- Ollama (Llama 3.2)
- Retrieval-Augmented Generation (RAG)
- FAISS Vector Database
- Sentence Transformers
- Semantic Similarity Search

---

# 🛠 Technology Stack

### Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js
- Font Awesome

### Backend

- Python
- Flask

### AI

- Ollama
- Llama 3.2
- Sentence Transformers
- FAISS

---

# 📂 Project Structure

```
AI-Smart-Bug-Analyzer/

│── app.py
│── bug_reports.csv
│── build_vector_db.py
│── preprocess.py
│── README.md

├── dataset/
│     └── mozilla/
│            ├── clean_mozilla.csv
│            └── mozilla_bugs.csv

├── templates/
│     ├── index.html
│     └── result.html

├── static/
│     ├── style.css
│     └── script.js

├── uploads/

├── analysis_results/

├── utils/
│     ├── triage_agent.py
│     ├── log_analysis.py
│     ├── root_cause_agent.py
│     ├── duplicate_detection.py
│     └── remediation_agent.py
```

---

# ⚙ Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Smart-Bug-Analyzer.git
```

Move into project

```bash
cd AI-Smart-Bug-Analyzer
```

Create Virtual Environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Install requirements

```bash
pip install -r requirements.txt
```

Run

```bash
python app.py
```

Open

```
http://127.0.0.1:5000
```

---

# 🔄 Workflow

1. Upload Bug Report
2. Upload Log File (Optional)
3. AI Triage Analysis
4. Log Analysis
5. Root Cause Detection
6. Duplicate Detection
7. Remediation Recommendation
8. Analytics Dashboard
9. Download Report

---

# 📊 Dashboard Modules

- Executive Summary
- Bug Information
- AI Triage
- Root Cause Analysis
- Log Analysis
- Duplicate Detection
- Remediation
- Analytics Dashboard
- Reports

---

# 🎯 Key Highlights

- AI-Based Multi-Agent Architecture
- Retrieval-Augmented Generation (RAG)
- Historical Bug Retrieval
- Semantic Similarity Search
- Interactive Dashboard
- Enterprise UI
- JSON Report Generation
- Print Support
- Analytics Charts
- Intelligent Bug Resolution

---

# 📈 Future Enhancements

- PDF Report Download
- Email Notifications
- Jira Integration
- GitHub Issues Integration
- Docker Deployment
- Kubernetes Support
- Cloud Deployment (AWS/Azure/GCP)
- Multi-Language Bug Analysis
- Real-Time Bug Monitoring

---

# 👩‍💻 Developed By

**Vyshnavi Polavarapu**

B.Tech (CSE - AI & ML)

AI Smart Bug Analyzer & Fix Advisor

2026

---

# 📄 License

This project is developed for educational and research purposes.