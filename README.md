# 🐞 AI Smart Bug Analyzer & Intelligent Fix Advisor

## 📌 Project Overview

AI Smart Bug Analyzer & Intelligent Fix Advisor is a Retrieval-Augmented Generation (RAG)-based web application that assists software developers in analyzing software bugs. The system retrieves similar historical bugs from the Mozilla Bug Dataset using FAISS vector search and generates intelligent offline fix recommendations without requiring any external API.

---

## 🚀 Features

- Submit software bug reports
- Upload screenshots or log files
- Store bug reports in CSV
- Semantic search using Sentence Transformers
- FAISS Vector Database for similarity search
- Retrieve Top 3 Similar Bugs
- Bug Category Prediction
- Priority Prediction
- Confidence Score
- Offline AI Smart Fix Advisor
- Root Cause Analysis
- Impact Analysis
- Recommended Fixes
- Testing Checklist
- Prevention Tips
- Attractive Result Dashboard

---

## 🏗️ System Architecture

User
↓

Flask Web Application

↓

Sentence Transformer (all-MiniLM-L6-v2)

↓

FAISS Vector Database

↓

Mozilla Bug Dataset

↓

Offline AI Recommendation Engine

↓

Result Dashboard

---

## 🔄 Workflow

1. User enters a bug description.
2. User optionally uploads a screenshot or log file.
3. Bug report is stored in CSV.
4. Sentence Transformer converts the bug report into vector embeddings.
5. FAISS retrieves the Top 3 most similar bugs.
6. Offline AI engine generates:
   - Bug Category
   - Priority
   - Confidence
   - Root Cause Analysis
   - Impact Analysis
   - Recommended Fix
   - Testing Checklist
   - Prevention Tips
7. Results are displayed on the dashboard.

---

## 💻 Technologies Used

- Python 3.11
- Flask
- HTML
- CSS
- FAISS
- Sentence Transformers
- Pandas
- NumPy
- Mozilla Bug Dataset

---

## 📂 Project Structure

AI-Smart-Bug-Analyzer

│

├── app.py

├── requirements.txt

├── bug_reports.csv

├── preprocess.py

├── build_vector_db.py

├── search_bug.py

│

├── dataset/

│ └── mozilla/

│ ├── clean_mozilla.csv

│ ├── mozilla_bugs.csv

│ └── bug_index.faiss

│

├── templates/

│ ├── index.html

│ └── result.html

│

├── uploads/

│

└── README.md

---

## ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Smart-Bug-Analyzer.git
```

Move into the project

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

Install packages

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

## 📸 Output

The application displays

- Bug Category
- Severity
- Priority
- Confidence Score
- Top 3 Similar Bugs
- Root Cause Analysis
- Impact Analysis
- Recommended Fix
- Testing Checklist
- Prevention Tips

---

## 📌 Future Scope

- User Authentication
- Bug Tracking Dashboard
- Admin Panel
- Email Notifications
- PDF Report Generation
- Cloud Deployment
- Machine Learning-based Bug Classification

---
