# AGENTS.md

本文件面向后续接手本项目的大模型 / Coding Agent。请先阅读本文件，再修改代码。

## 项目定位

PageStruct AI 是一个网页内容标准化解析系统，不是简单爬虫，也不是简单问答系统。

系统职责链：

```text
任务管理
→ 网页获取
→ 正文和附件链接提取
→ LLM 标准化
→ 数据库存档
→ 页面展示
→ TXT/DOCX 导出
```

## 当前完成状态

`pagestruct_ai_development_doc.md` 中第 0 到第 13 阶段均已完成：

- FastAPI + Jinja2 + HTMX 项目骨架
- SQLAlchemy + SQLite 模型
- 单条 URL 任务创建
- 任务列表和任务详情页
- 网页获取服务
- HTML 内容提取服务
- 单条 URL 完整解析
- 记录详情页
- LLM 标准化服务
- LLM 接入解析流程
- TXT / DOCX 导出
- CSV / XLSX 批量上传
- 批量任务串行执行
- 暂停和继续任务

## 必须遵守的核心原则

1. 不要让 LLM 直接访问网页。
2. 不要把 URL 直接丢给 LLM。
3. HTTP 状态、网络错误、超时、SSL 错误必须由程序判断。
4. LLM 只负责处理已经提取出来的 `clean_text` 和 `file_links`。
5. LLM 必须输出严格 JSON。
6. LLM 输出必须经过 `LLMResult` Pydantic 校验。
7. LLM 输出的附件 URL 必须来自输入的 `file_links`，否则丢弃。
8. 每条 URL 的解析状态必须保存到 `parse_record`。
9. 批量任务必须每条 URL 完成后立即提交数据库。
10. 暂停任务不要强杀当前记录，当前记录完成后再停止后续记录。
11. 继续任务只处理未完成记录，不要重复解析 `COMPLETED`。
12. Router 不要承载复杂业务逻辑，核心逻辑放到 service。

## 目录职责

```text
backend/app/main.py
```

FastAPI 应用入口，挂载静态资源、注册 router、应用启动时创建数据库表和执行轻量 schema 补丁。

```text
backend/app/config.py
```

应用配置，包括模板目录、静态目录和 LLM 环境变量。

```text
backend/app/database.py
```

SQLAlchemy engine、SessionLocal、Base、get_db，以及当前 SQLite schema 补丁。

```text
backend/app/models/
```

ORM 模型：

- `Task`
- `ParseRecord`
- `Attachment`
- `UploadFile`

```text
backend/app/routers/
```

页面路由、动作路由和下载路由：

- `task_router.py`
- `record_router.py`

```text
backend/app/services/
```

业务逻辑层：

- `fetch_service.py`：网页请求和结构化错误
- `extract_service.py`：HTML 标题、正文、链接、附件链接提取
- `llm_service.py`：LLM 调用、JSON 解析、Pydantic 校验、附件 URL 防编造
- `task_service.py`：单条/批量任务执行、暂停、继续、状态更新
- `docx_service.py`：TXT / DOCX 生成
- `file_service.py`：上传文件保存、CSV/XLSX 读取

```text
backend/app/templates/
```

Jinja2 页面和 HTMX partial。

```text
backend/storage/
```

运行时文件目录：

- `uploads/`：上传的 CSV/XLSX
- `txt/`：生成的 TXT
- `docx/`：生成的 DOCX

## 状态枚举

任务状态 `task.status`：

```text
PENDING
RUNNING
PAUSED
COMPLETED
FAILED
CANCELED
```

记录执行状态 `parse_record.execute_status`：

```text
PENDING
PROCESSING
COMPLETED
FAILED
SKIPPED
```

网页获取状态 `parse_record.fetch_status`：

```text
SUCCESS
INVALID_URL
TIMEOUT
HTTP_ERROR
NETWORK_ERROR
SSL_ERROR
UNKNOWN_ERROR
```

结果类型 `parse_record.result_type`：

```text
INVALID_PAGE
EMPTY_CONTENT
ONLY_FILES
ONLY_TEXT
TEXT_AND_FILES
FAILED
```

## 关键实现说明

### 任务执行

`task_service.parse_record()` 是单条记录解析的核心函数。它负责：

1. 设置 record 为 `PROCESSING`
2. 调用 `fetch_page`
3. 保存 fetch 状态
4. fetch 失败时写入 `FAILED` 和 `INVALID_PAGE`
5. fetch 成功时调用 `extract_page_content`
6. 保存标题、正文、附件
7. 调用 LLM 标准化
8. 生成 TXT / DOCX
9. 设置 record 为 `COMPLETED`

### 批量执行

`start_batch_task()`：

- 只处理 `PENDING` 记录。
- 按 `ParseRecord.id` 升序串行处理。
- 每条记录后调用 `refresh_task_counts()` 并提交数据库。
- 每条记录后重新读取 task 状态；如果变成 `PAUSED`，停止后续记录。

### LLM 失败处理

LLM 失败不应导致原始解析失败。当前策略：

- `llm_json` 保存 `FAILED` 结构。
- `error_message` 追加 LLM 错误。
- record 仍可保持 `COMPLETED`，只要 fetch 和 extract 成功。
- `result_type` 保持程序规则判断出的值。

### 导出

TXT / DOCX 在记录完成后生成，并保存路径：

- `parse_record.txt_file_path`
- `parse_record.docx_file_path`

只有 `COMPLETED` 记录允许下载。

## 当前技术债

1. 没有 Alembic，schema 迁移只有手动轻量补丁。
2. batch 执行目前在请求内同步完成，不是真后台任务。
3. 暂停操作在同步请求执行期间，需要另一个请求能更新数据库状态；后续更适合改为后台线程或任务队列。
4. 没有自动测试套件，当前主要靠 compileall 和手动 smoke test。
5. LLM 服务仅适配 OpenAI-compatible Chat Completions 返回格式。
6. 未做用户系统、权限系统、反爬、验证码、浏览器渲染、OCR、附件自动下载。

## 后续开发建议

优先级建议：

1. 增加 pytest 测试，覆盖 fetch、extract、llm schema、task 状态流转。
2. 引入 Alembic 管理数据库迁移。
3. 将 batch 执行改为后台线程或任务队列，避免长请求阻塞。
4. 为任务增加取消 `CANCELED` 的实际行为。
5. 为 LLM 服务增加 provider 抽象和更稳的 JSON 修复逻辑。
6. 增加文件大小限制和上传安全校验。
7. 增加结构化日志。

## 本地运行

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

如果虚拟环境不存在：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 验证命令

```bash
cd backend
PYTHONPYCACHEPREFIX=/tmp/pagestruct_pycache .venv/bin/python -m compileall app
.venv/bin/python -c 'from app.main import app; print(app.title)'
curl http://127.0.0.1:8000/api/health
```

## 修改代码时的注意事项

- 保持分层：router 薄，service 厚。
- 不要在模板或 HTMX 中维护业务状态，状态必须来自数据库。
- 不要让 LLM 覆盖程序判断出的 HTTP 错误。
- 不要在 batch 中等全部完成才提交数据库。
- 不要重复解析已完成记录，除非明确新增“重新解析”功能。
- 不要把上传文件、导出文件路径暴露为任意文件下载入口，只允许下载系统生成的 TXT/DOCX。
- 兼容当前 Python 3.9 环境，类型注解避免使用运行时不兼容写法。
