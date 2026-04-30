# PageStruct AI

Chinese: [`README.zh-CN.md`](README.zh-CN.md)

PageStruct AI is a web content parsing, standardization, and archiving system. It accepts a single webpage URL or a CSV / Excel file containing multiple URLs, fetches each page, determines whether the page is valid, extracts the main text and attachment links, and then uses an LLM to standardize the extracted content into structured JSON. All task states and parsing results are stored in SQLite and displayed through a Jinja2 + HTMX web interface.

The current codebase implements the full MVP described in the development document, including single URL parsing, batch upload, batch execution, pause/resume, result detail pages, and TXT / DOCX downloads.

## What It Does

- Create a parsing task from a single URL.
- Upload CSV or XLSX files to create batch URL parsing tasks.
- Fetch webpages and store HTTP status, final URL, and error reasons.
- Extract page title, clean text, links, and attachment links from HTML.
- Detect common attachment types such as PDF, Word, Excel, PowerPoint, ZIP, TXT, and CSV.
- Call an OpenAI-compatible LLM API to standardize page content.
- Validate LLM output with Pydantic.
- Prevent the LLM from inventing attachment URLs.
- Store each URL parsing record in the database.
- View tasks, progress, records, extracted text, and attachments in the web UI.
- Export completed records as TXT and DOCX.
- Pause and resume batch tasks.

## Tech Stack

Backend:

- Python
- FastAPI
- SQLAlchemy
- SQLite
- requests
- BeautifulSoup4
- pandas
- openpyxl
- python-docx

Frontend:

- Jinja2
- HTMX
- CSS
- Minimal vanilla JavaScript

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
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── database.py
    │   ├── models/
    │   ├── routers/
    │   ├── schemas/
    │   ├── services/
    │   ├── templates/
    │   ├── static/
    │   └── utils/
    └── storage/
        ├── uploads/
        ├── txt/
        └── docx/
```

## Local Setup

```bash
cd /Users/chinav/code_project/PageStruct_AI/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

If the virtual environment does not exist yet:

```bash
cd /Users/chinav/code_project/PageStruct_AI/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the app:

```text
http://127.0.0.1:8000
```

Common pages:

- Home: `http://127.0.0.1:8000/`
- Task list: `http://127.0.0.1:8000/tasks`
- Health check: `http://127.0.0.1:8000/api/health`

## LLM Configuration

The app automatically loads local environment files:

```text
.env
backend/.env
```

If both files exist, values in `backend/.env` take precedence over values in the project-root `.env`.

Create a local config file from the example:

```bash
cd backend
cp .env.example .env
```

Then fill in:

```env
LLM_API_KEY=your-api-key
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT=60
```

For a local OpenAI-compatible model server:

```env
LLM_API_KEY=local-dev-key
LLM_API_URL=http://127.0.0.1:8001/v1/chat/completions
LLM_MODEL=your-local-model-name
LLM_TIMEOUT=120
```

If `LLM_API_KEY` is not configured, the system can still fetch webpages, extract text, detect attachments, and export files. The LLM result will be saved as `FAILED`, and the error reason will be stored in the parsing record.

## Usage

### Single URL Parsing

1. Open `/`.
2. Enter a webpage URL in the single URL form.
3. Create the task.
4. Open the task detail page.
5. Click "Start Parsing".
6. Open the record detail page after completion.
7. View the extracted text, attachments, errors, and download TXT / DOCX files.

### Batch Parsing

1. Prepare a CSV or XLSX file.
2. Include a URL column, for example `网页链接`.
3. Upload the file on the home page and provide the URL column name.
4. Create the batch task.
5. Open the task detail page and click "Start Parsing".
6. Records are parsed sequentially by record ID.

### Pause and Resume

- A running batch task can be paused.
- Pausing does not forcefully interrupt the currently running URL.
- After the current record finishes, pending records will not start.
- Resuming only processes unfinished records and does not reprocess completed records.

## Main Routes

| Method | Path | Description |
|---|---|---|
| GET | `/` | Home page |
| GET | `/tasks` | Task list |
| GET | `/tasks/{task_id}` | Task detail |
| GET | `/records/{record_id}` | Record detail |
| POST | `/tasks/single` | Create a single URL task |
| POST | `/tasks/batch/upload` | Upload CSV / XLSX and create a batch task |
| POST | `/tasks/{task_id}/start` | Start a task |
| POST | `/tasks/{task_id}/pause` | Pause a task |
| POST | `/tasks/{task_id}/resume` | Resume a task |
| GET | `/records/{record_id}/download/txt` | Download TXT |
| GET | `/records/{record_id}/download/docx` | Download DOCX |

## Data Storage

Default database:

```text
backend/pagestruct_ai.db
```

Core tables:

- `task`: task metadata
- `parse_record`: per-URL parsing record
- `attachment`: extracted attachment links
- `upload_file`: uploaded file metadata

Runtime file directories:

```text
backend/storage/uploads/
backend/storage/txt/
backend/storage/docx/
```

## Core Processing Flow

```text
User submits a URL or uploads CSV / XLSX
        ↓
Create task and parse_record rows
        ↓
Start task
        ↓
fetch_service fetches the page
        ↓
extract_service extracts text and attachment links
        ↓
llm_service standardizes the content
        ↓
Save results to database
        ↓
docx_service generates TXT / DOCX
        ↓
Display and download through the web UI
```

## Design Constraints

- The LLM must not fetch webpages directly.
- URLs must not be sent directly to the LLM as the primary parsing mechanism.
- HTTP status and network errors are determined by application code.
- The LLM only processes extracted text and attachment links.
- The LLM must output strict JSON.
- LLM output must pass Pydantic validation.
- Attachment URLs returned by the LLM must come from the original `file_links`.
- Batch tasks must save each record immediately after completion.
- Pausing a task must not forcefully kill the currently running record.
- Resuming a task must only process unfinished records.

## Verification Commands

```bash
cd backend
PYTHONPYCACHEPREFIX=/tmp/pagestruct_pycache .venv/bin/python -m compileall app
.venv/bin/python -c 'from app.main import app; print(app.title)'
curl http://127.0.0.1:8000/api/health
```

## Current Limitations

- Batch execution is synchronous and sequential; it can later be upgraded to a background worker or task queue.
- There is no user authentication or permission system.
- Advanced anti-bot handling, CAPTCHA solving, browser rendering, and OCR are not implemented.
- There is no Alembic migration system.
- LLM calls currently assume an OpenAI-compatible Chat Completions response format.
