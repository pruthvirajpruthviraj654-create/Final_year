# ExamAI v2 — AI-Powered Syllabus-Based Question Paper Generator

## Quick Start

```bash
cd examai-v2
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```
Open: **http://localhost:5000**

## Demo Credentials
| Role | Email | Password |
|------|-------|----------|
| Teacher | teacher@examai.edu | teacher123 |
| Admin | admin@examai.edu | admin123 |

## New in v2 — Syllabus Engine
1. **Upload Syllabus** → PDF/DOCX/TXT → AI extracts units & topics
2. **Manual Entry** → Paste syllabus text
3. **Built-in Topics** → 8 subjects with 200+ curated topics
4. **Generate** → Questions ONLY from your syllabus topics
5. **5 Marks Types** → MCQ(1M), Short(2M), Medium(5M), Descriptive(7M), Long(10M)
6. **Bloom's Taxonomy** → L1–L6 cognitive levels
7. **Duplicate Detection** → Semantic similarity scoring

## AI API Setup
1. Get free key at openrouter.ai
2. Dashboard → Settings → Paste API key
3. Select model (GPT-3.5 free, GPT-4 best)

## Project Structure
```
examai-v2/
├── app.py                  # Flask app factory
├── config.py               # Configuration
├── database.py             # DB + seeding
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── paper.py
│   ├── question.py
│   ├── syllabus.py         # NEW: Syllabus + Topic models
│   └── feedback.py
├── routes/                 # Flask blueprints
│   ├── auth.py
│   ├── paper.py
│   ├── qbank.py
│   ├── admin.py
│   ├── api.py
│   └── syllabus.py         # NEW: Upload/parse/manage
├── services/               # Business logic
│   ├── syllabus_engine.py  # NEW: PDF/DOCX/TXT parser
│   ├── prompt_engine.py    # NEW: Advanced AI prompts
│   ├── bloom_engine.py     # NEW: Bloom taxonomy mapping
│   ├── difficulty_engine.py# NEW: Difficulty + marks config
│   ├── duplicate_checker.py# NEW: Semantic dedup
│   ├── ai_service.py       # AI generation (OpenRouter)
│   └── pdf_service.py      # ReportLab PDF
├── templates/              # HTML pages
├── static/css/style.css
├── static/js/app.js
└── requirements.txt
```
