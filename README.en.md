# PageStruct AI

Chinese: [`README.zh-CN.md`](README.zh-CN.md)

PageStruct AI is a web content parsing, standardization, and archiving system. It provides the infrastructure for fetching web pages, extracting clean text, and managing structured data.

> **Note:** The LLM integration and web application (`backend/app/`) have been removed. The five-year plan crawler has been moved to a [separate repository](https://github.com/y2362262019-dot/five_year_plan_crawler).

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- requests
- BeautifulSoup4
- pandas
- openpyxl
- python-docx

## Project Structure

```text
PageStruct_AI/
├── README.md
├── README.en.md
├── README.zh-CN.md
├── AGENTS.md
├── pagestruct_ai_development_doc.md
└── backend/
    ├── README.md
    ├── requirements.txt
    ├── .venv/
    ├── storage/
    │   ├── uploads/
    │   ├── txt/
    │   └── docx/
    └── data/
```

## Local Setup

```bash
cd /Users/chinav/code_project/PageStruct_AI/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data Storage

Default database:

```text
backend/pagestruct_ai.db
```

Runtime file directories:

```text
backend/storage/uploads/
backend/storage/txt/
backend/storage/docx/
```
