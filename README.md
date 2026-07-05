# 🤖 AI Smart Bug Analyzer & Fix Advisor

## 📌 Project Overview

AI Smart Bug Analyzer & Fix Advisor is an AI-powered web application that helps developers analyze software bug reports. It uses Retrieval-Augmented Generation (RAG) by combining Sentence Transformers, FAISS Vector Database, and Google Gemini AI to retrieve similar historical bugs and generate intelligent fix suggestions.

---

## 🚀 Features

- 📝 Submit software bug reports
- 📂 Upload bug report files (.txt, .log, .pdf)
- 📊 Store submitted bugs in CSV format
- 🧹 Clean Mozilla Bug Dataset
- 🔍 Find Top 5 Similar Bugs using FAISS
- 🤖 Generate AI-powered fix suggestions using Gemini AI
- 🌐 User-friendly Flask web interface
- ⚡ Retrieval-Augmented Generation (RAG) implementation

---

## 🛠️ Technologies Used

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- Pandas
- NumPy
- Sentence Transformers
- FAISS
- Google Gemini AI
- Git
- GitHub

---

## 🧠 AI Workflow

1. User submits a bug report.
2. Flask receives the request.
3. The bug report is converted into embeddings using Sentence Transformers.
4. FAISS retrieves the Top 5 similar bug reports.
5. Retrieved bugs are sent to Gemini AI.
6. Gemini generates intelligent fix suggestions.
7. Results are displayed on the web page.

---

## 📂 Project Structure

```text
AI-Smart-Bug-Analyzer/
│
├── dataset/
│   └── mozilla/
│       ├── mozilla_bugs.csv
│       ├── clean_mozilla.csv
│       └── bug_index.faiss
│
├── docs/
│
├── static/
│   ├── style.css
│   └── script.js
│
├── templates/
│   ├── index.html
│   └── result.html
│
├── uploads/
│
├── app.py
├── preprocess.py
├── build_vector_db.py
├── search_bug.py
├── bug_reports.csv
├── requirements.txt
└── README.md
```

---

## 🔄 System Architecture

User

↓

Flask Web Application

↓

Sentence Transformer (all-MiniLM-L6-v2)

↓

FAISS Vector Database

↓

Top 5 Similar Bugs Retrieved

↓

Gemini AI

↓

AI Suggested Fix

↓

Result Page

---

## 📊 Dataset

- Mozilla Bug Reports Dataset
- Cleaned using Pandas
- Bug Descriptions
- Severity Levels

---

## 🧠 RAG Pipeline

- User Query
- Sentence Transformer Embedding
- FAISS Similarity Search
- Retrieve Relevant Bugs
- Gemini AI Response Generation

---

## ▶️ Installation

Clone the repository

```bash
git clone https://github.com/vyshnavipolavarapuu/AI-Smart-Bug-Analyzer.git
```

Open the project

```bash
cd AI-Smart-Bug-Analyzer
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python app.py
```

Open

```
http://127.0.0.1:5000
```

---

## 📷 Screenshots

### Home Page

(Add screenshot here)

### Result Page

(Add screenshot here)

### AI Suggested Fix

(Add screenshot here)

---

## 🎯 Future Enhancements

- User Authentication
- Bug Severity Prediction
- Bug Classification
- PDF Report Generation
- Dashboard Analytics
- Cloud Deployment
- Database Integration

---

## 👩‍💻 Developer

**Vyshnavi Polavarapu**

B.Tech CSE (AI & ML)

AI Smart Bug Analyzer & Fix Advisor

---

## ⭐ Acknowledgements

- Mozilla Bug Dataset
- Sentence Transformers
- FAISS
- Google Gemini AI
- Flask