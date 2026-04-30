# PageStruct AI

PageStruct AI 是一个基于网页抓取、内容提取和大模型标准化的网页内容解析系统。系统支持单条 URL 解析，也支持上传 CSV / Excel 文件批量创建解析任务。每条 URL 的抓取状态、正文、附件链接、大模型标准化结果和导出文件都会保存到 SQLite 数据库中，并通过 Jinja2 + HTMX 页面展示。

当前代码已经完成开发文档中的第 0 到第 13 阶段，属于可运行的 MVP。

## 已实现能力

- 单条 URL 任务创建
- CSV / XLSX 批量上传并创建 batch 任务
- 单条和批量任务启动解析
- 批量任务串行执行
- 批量任务暂停和继续
- HTTP 状态、网络错误、SSL 错误、超时等结构化保存
- HTML 标题、正文、普通链接和附件链接提取
- 大模型标准化服务，要求严格 JSON 输出
- Pydantic 校验 LLM 输出
- 防止大模型编造附件 URL
- 解析记录详情页
- TXT / DOCX 导出与下载
- HTMX 局部刷新任务列表、任务进度和记录表格

## 技术栈

后端：

- Python
- FastAPI
- SQLAlchemy
- SQLite
- requests
- BeautifulSoup4
- pandas
- openpyxl
- python-docx

前端：

- Jinja2
- HTMX
- 原生 CSS
- 少量原生 JavaScript

## 项目结构

```text
PageStruct_AI/
├── README.md
├── AGENTS.md
├── pagestruct_ai_development_doc.md
└── backend/
    ├── README.md
    ├── requirements.txt
    ├── pagestruct_ai.db
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

## 快速启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问：

- 首页：`http://127.0.0.1:8000/`
- 任务列表：`http://127.0.0.1:8000/tasks`
- 健康检查：`http://127.0.0.1:8000/api/health`

## 大模型配置

系统的大模型调用使用 OpenAI-compatible Chat Completions 接口。

项目启动时会自动读取以下本地配置文件：

```text
.env
backend/.env
```

如果两个文件都存在，`backend/.env` 中的同名配置会覆盖项目根目录 `.env`。

可以复制示例文件后修改：

```bash
cd backend
cp .env.example .env
```

`backend/.env` 示例：

```bash
LLM_API_KEY=your-api-key
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT=60
```

如果没有配置 `LLM_API_KEY`，系统仍会完成网页抓取、正文提取、附件识别和文件导出。此时 `llm_json` 会保存一个 `FAILED` 类型的结果，`error_message` 会记录 LLM 配置缺失原因。

本地 OpenAI-compatible 模型服务示例：

```env
LLM_API_KEY=local-dev-key
LLM_API_URL=http://127.0.0.1:8001/v1/chat/completions
LLM_MODEL=your-local-model-name
LLM_TIMEOUT=120
```

## 使用流程

### 单条 URL

1. 打开首页 `/`。
2. 在“单条 URL 解析”输入框中输入 `http://` 或 `https://` 开头的链接。
3. 创建任务。
4. 进入任务详情页。
5. 点击“开始解析”。
6. 等待任务完成后点击记录详情。
7. 查看正文、附件列表、错误信息、下载 TXT / DOCX。

### 批量上传

1. 准备 CSV 或 XLSX 文件。
2. 文件中需要有一列保存 URL，例如 `网页链接`。
3. 打开首页 `/`。
4. 上传文件并填写 URL 列名。
5. 创建 batch 任务。
6. 进入任务详情页并点击“开始解析”。
7. 批量任务会按记录 ID 顺序串行解析。

### 暂停和继续

- batch 任务运行时可以点击“暂停”。
- 暂停不会强制中断当前正在解析的 URL。
- 当前记录完成后，后续 PENDING 记录不会继续开始。
- 点击“继续”后，只会处理未完成记录，不会重复解析已完成记录。

## 主要路由

页面路由：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 首页 |
| GET | `/tasks` | 任务列表 |
| GET | `/tasks/{task_id}` | 任务详情 |
| GET | `/records/{record_id}` | 记录详情 |

HTMX partial：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/tasks/partials/table` | 任务表格 |
| GET | `/tasks/{task_id}/partials/progress` | 任务进度 |
| GET | `/tasks/{task_id}/partials/records` | 任务记录表格 |

动作路由：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/tasks/single` | 创建单条任务 |
| POST | `/tasks/batch/upload` | 上传 CSV / XLSX 并创建批量任务 |
| POST | `/tasks/{task_id}/start` | 启动任务 |
| POST | `/tasks/{task_id}/pause` | 暂停任务 |
| POST | `/tasks/{task_id}/resume` | 继续任务 |
| GET | `/records/{record_id}/download/txt` | 下载 TXT |
| GET | `/records/{record_id}/download/docx` | 下载 DOCX |

## 数据库

默认使用 SQLite：

```text
backend/pagestruct_ai.db
```

核心表：

- `task`：任务信息，支持 single / batch
- `parse_record`：每条 URL 的解析状态和结果
- `attachment`：网页中提取到的附件链接
- `upload_file`：批量上传文件元数据

应用启动时会自动创建表。当前代码还包含一个轻量 schema 补丁，用于给已有 SQLite 数据库补充 `parse_record.main_content` 列。

## 核心流程

```text
用户提交 URL 或上传 CSV/XLSX
        ↓
创建 task 和 parse_record
        ↓
用户启动任务
        ↓
fetch_service 访问网页
        ↓
extract_service 提取标题、正文、链接、附件链接
        ↓
llm_service 标准化正文和附件信息
        ↓
保存数据库
        ↓
docx_service 生成 TXT / DOCX
        ↓
Jinja2 + HTMX 页面展示和下载
```

## 设计约束

- 大模型不直接访问网页。
- HTTP 状态、网络错误、超时等由程序判断。
- LLM 只处理已经提取出来的文本和附件链接。
- LLM 输出必须是严格 JSON。
- LLM 输出必须经过 Pydantic 校验。
- LLM 输出的附件 URL 必须来自原始 `file_links`，否则丢弃。
- 批量任务每条 URL 解析完成后立即保存。
- 暂停任务不强杀正在解析的记录。
- 继续任务只处理未完成记录。
- 第一版不做登录、权限、验证码、复杂反爬、并发解析、附件自动下载。

## 导出文件

系统生成文件保存在：

```text
backend/storage/txt/
backend/storage/docx/
```

上传文件保存在：

```text
backend/storage/uploads/
```

只有 `COMPLETED` 状态的记录允许下载 TXT / DOCX。

## 开发验证命令

```bash
cd backend
PYTHONPYCACHEPREFIX=/tmp/pagestruct_pycache .venv/bin/python -m compileall app
.venv/bin/python -c 'from app.main import app; print(app.title)'
```

启动后可用 curl 做 smoke test：

```bash
curl http://127.0.0.1:8000/api/health
curl -I http://127.0.0.1:8000/
curl -I http://127.0.0.1:8000/tasks
```

## 当前限制

- batch 执行是串行同步执行，请求会等待任务结束；后续可升级为后台线程或任务队列。
- 未实现用户登录和权限控制。
- 未实现复杂反爬、验证码处理、浏览器渲染、OCR 或附件自动下载。
- 没有 Alembic 迁移系统，当前 SQLite schema 主要依赖 `create_all` 和少量手写补丁。
- LLM 调用目前按 OpenAI-compatible Chat Completions 响应格式解析。
