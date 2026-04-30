from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile as FastAPIUploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.parse_record import ParseRecord
from app.models.task import Task
from app.models.upload_file import UploadFile
from app.services.file_service import get_file_type, read_url_rows, save_upload_file
from app.services.task_service import pause_task, resume_task, start_task_run
from app.utils.url_utils import is_http_url


router = APIRouter(prefix="/tasks", tags=["tasks"])
templates = Jinja2Templates(directory=get_settings().templates_dir)


@router.get("", response_class=HTMLResponse)
def task_list(request: Request, db: Session = Depends(get_db)):
    tasks = db.scalars(select(Task).order_by(Task.created_at.desc())).all()
    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "page_title": "任务列表",
            "tasks": tasks,
        },
    )


@router.get("/partials/table", response_class=HTMLResponse)
def task_table(request: Request, db: Session = Depends(get_db)):
    tasks = db.scalars(select(Task).order_by(Task.created_at.desc())).all()
    return templates.TemplateResponse(
        "partials/task_table.html",
        {
            "request": request,
            "tasks": tasks,
        },
    )


@router.get("/{task_id}", response_class=HTMLResponse)
def task_detail(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.scalar(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.records).selectinload(ParseRecord.attachments))
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    records = sorted(task.records, key=lambda item: item.id)
    return templates.TemplateResponse(
        "task_detail.html",
        {
            "request": request,
            "page_title": "任务详情",
            "task": task,
            "records": records,
        },
    )


@router.get("/{task_id}/partials/records", response_class=HTMLResponse)
def record_table(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    records = db.scalars(
        select(ParseRecord)
        .where(ParseRecord.task_id == task_id)
        .options(selectinload(ParseRecord.attachments))
        .order_by(ParseRecord.id.asc())
    ).all()
    return templates.TemplateResponse(
        "partials/record_table.html",
        {
            "request": request,
            "task": task,
            "records": records,
        },
    )


@router.get("/{task_id}/partials/progress", response_class=HTMLResponse)
def task_progress(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return templates.TemplateResponse(
        "partials/task_progress.html",
        {
            "request": request,
            "task": task,
        },
    )


@router.post("/{task_id}/start", response_class=HTMLResponse)
def start_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    success, message = start_task_run(db, task)
    return templates.TemplateResponse(
        "partials/flash_message.html",
        {
            "request": request,
            "message_type": "success" if success else "error",
            "message": message,
            "task": task,
        },
        status_code=200 if success else 400,
    )


@router.post("/{task_id}/pause", response_class=HTMLResponse)
def pause_task_route(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    success, message = pause_task(db, task)
    return templates.TemplateResponse(
        "partials/flash_message.html",
        {
            "request": request,
            "message_type": "success" if success else "error",
            "message": message,
            "task": task,
        },
        status_code=200 if success else 400,
    )


@router.post("/{task_id}/resume", response_class=HTMLResponse)
def resume_task_route(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    success, message = resume_task(db, task)
    return templates.TemplateResponse(
        "partials/flash_message.html",
        {
            "request": request,
            "message_type": "success" if success else "error",
            "message": message,
            "task": task,
        },
        status_code=200 if success else 400,
    )


@router.post("/single", response_class=HTMLResponse)
def create_single_task(
    request: Request,
    url: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_url = url.strip()
    if not is_http_url(normalized_url):
        return templates.TemplateResponse(
            "partials/flash_message.html",
            {
                "request": request,
                "message_type": "error",
                "message": "URL 格式不正确，请输入以 http:// 或 https:// 开头的网页链接。",
            },
            status_code=400,
        )

    task = Task(
        task_name=f"单条解析：{normalized_url[:80]}",
        task_type="single",
        status="PENDING",
        total_count=1,
        completed_count=0,
        failed_count=0,
    )
    db.add(task)
    db.flush()

    record = ParseRecord(
        task_id=task.id,
        url=normalized_url,
        execute_status="PENDING",
    )
    db.add(record)
    db.commit()
    db.refresh(task)

    return templates.TemplateResponse(
        "partials/flash_message.html",
        {
            "request": request,
            "message_type": "success",
            "message": "单条解析任务创建成功。",
            "task": task,
        },
    )


@router.post("/batch/upload", response_class=HTMLResponse)
async def create_batch_task(
    request: Request,
    file: FastAPIUploadFile = File(...),
    url_column: str = Form(...),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    file_type = get_file_type(filename)
    if not file_type:
        return templates.TemplateResponse(
            "partials/flash_message.html",
            {
                "request": request,
                "message_type": "error",
                "message": "文件格式不支持，请上传 CSV 或 XLSX 文件。",
            },
            status_code=400,
        )

    content = await file.read()
    if not content:
        return templates.TemplateResponse(
            "partials/flash_message.html",
            {
                "request": request,
                "message_type": "error",
                "message": "上传文件为空。",
            },
            status_code=400,
        )

    file_path = save_upload_file(filename, content)
    try:
        urls, total_rows = read_url_rows(file_path, file_type, url_column.strip())
    except ValueError as exc:
        return templates.TemplateResponse(
            "partials/flash_message.html",
            {
                "request": request,
                "message_type": "error",
                "message": str(exc),
            },
            status_code=400,
        )

    if not urls:
        return templates.TemplateResponse(
            "partials/flash_message.html",
            {
                "request": request,
                "message_type": "error",
                "message": "未在指定列中找到有效的 http:// 或 https:// URL。",
            },
            status_code=400,
        )

    task = Task(
        task_name=f"批量解析：{filename}",
        task_type="batch",
        status="PENDING",
        total_count=len(urls),
        completed_count=0,
        failed_count=0,
    )
    db.add(task)
    db.flush()

    upload_file = UploadFile(
        task_id=task.id,
        original_filename=filename,
        file_path=file_path,
        file_type=file_type,
        url_column=url_column.strip(),
        total_rows=total_rows,
    )
    db.add(upload_file)

    for url in urls:
        db.add(
            ParseRecord(
                task_id=task.id,
                url=url,
                execute_status="PENDING",
            )
        )

    db.commit()
    db.refresh(task)

    return templates.TemplateResponse(
        "partials/flash_message.html",
        {
            "request": request,
            "message_type": "success",
            "message": f"批量任务创建成功，共导入 {len(urls)} 条有效 URL。",
            "task": task,
        },
    )
