from fastapi import APIRouter, Depends, HTTPException, Request
from pathlib import Path
from typing import Optional

from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import get_db
from app.models.parse_record import ParseRecord


router = APIRouter(prefix="/records", tags=["records"])
templates = Jinja2Templates(directory=get_settings().templates_dir)


@router.get("/{record_id}", response_class=HTMLResponse)
def record_detail(record_id: int, request: Request, db: Session = Depends(get_db)):
    record = db.scalar(
        select(ParseRecord)
        .where(ParseRecord.id == record_id)
        .options(selectinload(ParseRecord.attachments), selectinload(ParseRecord.task))
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    return templates.TemplateResponse(
        "record_detail.html",
        {
            "request": request,
            "page_title": "记录详情",
            "record": record,
        },
    )


def _get_completed_record(record_id: int, db: Session) -> ParseRecord:
    record = db.get(ParseRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.execute_status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Only completed records can be downloaded")
    return record


def _download_generated_file(file_path: Optional[str], media_type: str) -> FileResponse:
    if not file_path:
        raise HTTPException(status_code=404, detail="Generated file not found")

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Generated file not found")

    return FileResponse(
        path,
        media_type=media_type,
        filename=path.name,
    )


@router.get("/{record_id}/download/txt")
def download_txt(record_id: int, db: Session = Depends(get_db)):
    record = _get_completed_record(record_id, db)
    return _download_generated_file(record.txt_file_path, "text/plain; charset=utf-8")


@router.get("/{record_id}/download/docx")
def download_docx(record_id: int, db: Session = Depends(get_db)):
    record = _get_completed_record(record_id, db)
    return _download_generated_file(
        record.docx_file_path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
