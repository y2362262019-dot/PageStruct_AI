from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.parse_record import ParseRecord
from app.models.task import Task
from app.services.extract_service import extract_page_content
from app.services.fetch_service import fetch_page
from app.services.llm_service import standardize_page_content
from app.services.docx_service import generate_record_exports


ALLOWED_RESULT_TYPES = {
    "INVALID_PAGE",
    "EMPTY_CONTENT",
    "ONLY_FILES",
    "ONLY_TEXT",
    "TEXT_AND_FILES",
    "FAILED",
}


def determine_result_type(clean_text: str, file_links: list[dict[str, str]]) -> str:
    has_text = bool(clean_text.strip())
    has_files = bool(file_links)

    if not has_text and not has_files:
        return "EMPTY_CONTENT"
    if not has_text and has_files:
        return "ONLY_FILES"
    if has_text and not has_files:
        return "ONLY_TEXT"
    return "TEXT_AND_FILES"


def refresh_task_counts(db: Session, task: Task) -> None:
    records = db.scalars(select(ParseRecord).where(ParseRecord.task_id == task.id)).all()
    task.completed_count = sum(1 for record in records if record.execute_status == "COMPLETED")
    task.failed_count = sum(1 for record in records if record.execute_status == "FAILED")

    finished_count = task.completed_count + task.failed_count
    if finished_count >= task.total_count:
        task.status = "COMPLETED" if task.failed_count == 0 else "FAILED"


def _finish_batch_task(db: Session, task: Task) -> None:
    refresh_task_counts(db, task)
    finished_count = task.completed_count + task.failed_count
    if finished_count >= task.total_count:
        task.status = "COMPLETED"
    db.commit()


def _has_unfinished_records(db: Session, task: Task) -> bool:
    return (
        db.scalar(
            select(ParseRecord.id)
            .where(ParseRecord.task_id == task.id)
            .where(ParseRecord.execute_status.in_(["PENDING", "PROCESSING"]))
            .limit(1)
        )
        is not None
    )


def _append_error(record: ParseRecord, message: str) -> None:
    if record.error_message:
        record.error_message = f"{record.error_message}\n{message}"
    else:
        record.error_message = message


def _apply_llm_result(record: ParseRecord, extracted: dict) -> None:
    if not extracted["clean_text"].strip() and not extracted["file_links"]:
        return

    llm_result = standardize_page_content(
        {
            "source_url": record.final_url or record.url,
            "html_title": record.title or "",
            "clean_text": extracted["clean_text"],
            "file_links": extracted["file_links"],
        }
    )
    record.llm_json = json.dumps(llm_result.model_dump(), ensure_ascii=False)

    if llm_result.result_type == "FAILED":
        _append_error(record, f"LLM: {llm_result.invalid_reason or 'standardization failed'}")
        return

    record.summary = llm_result.summary
    record.main_content = llm_result.main_content
    if llm_result.title:
        record.title = llm_result.title
    if llm_result.result_type in ALLOWED_RESULT_TYPES:
        record.result_type = llm_result.result_type


def parse_record(db: Session, record: ParseRecord) -> None:
    record.execute_status = "PROCESSING"
    record.started_at = datetime.utcnow()
    record.error_message = None
    db.commit()

    try:
        fetch_result = fetch_page(record.url)
        record.fetch_json = json.dumps(
            {key: value for key, value in fetch_result.items() if key != "html"},
            ensure_ascii=False,
        )
        record.fetch_status = fetch_result["fetch_status"]
        record.http_status = fetch_result["http_status"]
        record.final_url = fetch_result["final_url"]

        if fetch_result["fetch_status"] != "SUCCESS":
            record.execute_status = "FAILED"
            record.result_type = "INVALID_PAGE"
            record.error_message = fetch_result["error_message"]
            record.completed_at = datetime.utcnow()
            db.commit()
            return

        extracted = extract_page_content(
            fetch_result["html"],
            fetch_result["final_url"] or record.url,
        )
        record.title = extracted["title"]
        record.raw_text = extracted["raw_text"]
        record.clean_text = extracted["clean_text"]
        record.result_type = determine_result_type(
            extracted["clean_text"],
            extracted["file_links"],
        )

        for file_link in extracted["file_links"]:
            record.attachments.append(
                Attachment(
                    file_name=file_link["file_name"],
                    file_type=file_link["file_type"],
                    file_url=file_link["url"],
                    link_text=file_link["text"],
                )
            )

        _apply_llm_result(record, extracted)

        record.execute_status = "COMPLETED"
        record.completed_at = datetime.utcnow()
        db.flush()
        txt_path, docx_path = generate_record_exports(record)
        record.txt_file_path = txt_path
        record.docx_file_path = docx_path
        db.commit()
    except Exception as exc:
        db.rollback()
        record.execute_status = "FAILED"
        record.result_type = "FAILED"
        record.error_message = str(exc)
        record.completed_at = datetime.utcnow()
        db.add(record)
        db.commit()


def start_single_task(db: Session, task: Task) -> tuple[bool, str]:
    if task.task_type != "single":
        return False, "当前阶段只支持启动 single 类型任务。"
    if task.status in {"RUNNING", "COMPLETED", "PAUSED"}:
        return False, f"任务当前状态为 {task.status}，无需重复启动。"

    record = db.scalar(
        select(ParseRecord)
        .where(ParseRecord.task_id == task.id)
        .order_by(ParseRecord.id.asc())
    )
    if record is None:
        task.status = "FAILED"
        task.failed_count = task.total_count
        db.commit()
        return False, "任务没有可解析记录。"

    task.status = "RUNNING"
    db.commit()

    parse_record(db, record)
    db.refresh(task)
    refresh_task_counts(db, task)
    db.commit()

    return True, "任务解析已完成。"


def start_batch_task(db: Session, task: Task) -> tuple[bool, str]:
    if task.task_type != "batch":
        return False, "当前任务不是 batch 类型。"
    if task.status in {"RUNNING", "COMPLETED", "PAUSED"}:
        return False, f"任务当前状态为 {task.status}，无需重复启动。"

    pending_records = db.scalars(
        select(ParseRecord)
        .where(ParseRecord.task_id == task.id)
        .where(ParseRecord.execute_status == "PENDING")
        .order_by(ParseRecord.id.asc())
    ).all()
    if not pending_records:
        _finish_batch_task(db, task)
        return False, "任务没有待解析记录。"

    task.status = "RUNNING"
    db.commit()

    for record in pending_records:
        parse_record(db, record)
        db.refresh(task)
        refresh_task_counts(db, task)
        db.commit()
        db.refresh(task)
        if task.status == "PAUSED":
            return True, "任务已暂停，当前记录已完成，后续记录暂不解析。"

    _finish_batch_task(db, task)
    return True, "批量任务解析已完成。"


def start_task_run(db: Session, task: Task) -> tuple[bool, str]:
    if task.task_type == "single":
        return start_single_task(db, task)
    if task.task_type == "batch":
        return start_batch_task(db, task)
    return False, f"不支持的任务类型：{task.task_type}"


def pause_task(db: Session, task: Task) -> tuple[bool, str]:
    if task.status != "RUNNING":
        return False, f"任务当前状态为 {task.status}，不能暂停。"

    task.status = "PAUSED"
    task.paused_at = datetime.utcnow()
    db.commit()
    return True, "任务已暂停。当前正在解析的记录会先完成，后续记录不会继续开始。"


def resume_task(db: Session, task: Task) -> tuple[bool, str]:
    if task.status != "PAUSED":
        return False, f"任务当前状态为 {task.status}，不能继续。"

    if task.task_type == "single":
        task.status = "PENDING"
        task.paused_at = None
        db.commit()
        return start_single_task(db, task)

    if task.task_type == "batch":
        if not _has_unfinished_records(db, task):
            _finish_batch_task(db, task)
            return False, "任务没有未完成记录。"
        task.status = "PENDING"
        task.paused_at = None
        db.commit()
        return start_batch_task(db, task)

    return False, f"不支持的任务类型：{task.task_type}"
