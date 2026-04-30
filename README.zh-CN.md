# PageStruct AI 中文说明

English: [`README.en.md`](README.en.md)

PageStruct AI 是一个网页内容解析、标准化和归档工具。它可以接收单个网页链接，也可以通过 CSV / Excel 批量导入链接，然后自动访问网页、判断页面状态、提取正文和附件链接，再调用大模型把内容整理成结构化 JSON。所有解析过程和结果都会保存到 SQLite 数据库，并通过 Jinja2 + HTMX 构建的网页后台展示。

当前项目已经完成 MVP 功能，包括单条解析、批量上传、批量执行、暂停继续、结果查看和 TXT / DOCX 下载。

## 项目能做什么

- 输入一个 URL，创建单条解析任务。
- 上传 CSV 或 XLSX 文件，批量创建 URL 解析任务。
- 自动请求网页并记录 HTTP 状态、最终 URL、错误原因。
- 从 HTML 中提取网页标题、正文文本、普通链接和附件链接。
- 识别 PDF、Word、Excel、PPT、ZIP、TXT、CSV 等常见附件链接。
- 调用 OpenAI-compatible 大模型接口，对正文和附件进行标准化整理。
- 校验大模型输出的 JSON，防止模型编造附件 URL。
- 将每条 URL 的解析状态和结果保存到数据库。
- 在网页端查看任务进度、记录详情、正文和附件。
- 将解析结果导出为 TXT 和 DOCX。
- 批量任务支持暂停和继续。

## 技术架构

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
- CSS
- 少量原生 JavaScript

## 目录结构

```text
PageStruct_AI/
├── README.md
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

## 本地启动

```bash
cd /Users/chinav/code_project/PageStruct_AI/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

如果还没有虚拟环境：

```bash
cd /Users/chinav/code_project/PageStruct_AI/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000
```

常用页面：

- 首页：`http://127.0.0.1:8000/`
- 任务列表：`http://127.0.0.1:8000/tasks`
- 健康检查：`http://127.0.0.1:8000/api/health`

## 大模型配置

项目会自动读取以下配置文件：

```text
.env
backend/.env
```

如果两个文件都存在，`backend/.env` 的同名配置优先。

可以复制示例文件：

```bash
cd backend
cp .env.example .env
```

然后填写：

```env
LLM_API_KEY=your-api-key
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT=60
```

如果使用本地 OpenAI-compatible 模型服务，可以类似这样配置：

```env
LLM_API_KEY=local-dev-key
LLM_API_URL=http://127.0.0.1:8001/v1/chat/completions
LLM_MODEL=your-local-model-name
LLM_TIMEOUT=120
```

如果不配置 `LLM_API_KEY`，系统仍然可以完成网页抓取、正文提取、附件识别和文件导出，只是大模型标准化结果会保存为 `FAILED`，错误原因会写入记录。

## 使用方式

### 单条 URL 解析

1. 打开首页 `/`。
2. 在“单条 URL 解析”中输入网页链接。
3. 点击创建任务。
4. 进入任务详情页。
5. 点击“开始解析”。
6. 解析完成后进入记录详情页。
7. 查看正文、附件、错误信息，并下载 TXT / DOCX。

### 批量解析

1. 准备 CSV 或 XLSX 文件。
2. 文件中包含 URL 列，例如 `网页链接`。
3. 在首页上传文件并填写 URL 列名。
4. 创建批量任务。
5. 进入任务详情页并点击“开始解析”。
6. 系统会按记录 ID 顺序串行解析。

### 暂停和继续

- 批量任务运行中可以点击“暂停”。
- 暂停不会强制中断当前正在解析的 URL。
- 当前 URL 完成后，后续待处理 URL 不再开始。
- 点击“继续”后，只处理未完成记录，不会重复解析已完成记录。

## 主要路由

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 首页 |
| GET | `/tasks` | 任务列表 |
| GET | `/tasks/{task_id}` | 任务详情 |
| GET | `/records/{record_id}` | 记录详情 |
| POST | `/tasks/single` | 创建单条任务 |
| POST | `/tasks/batch/upload` | 上传 CSV / XLSX 创建批量任务 |
| POST | `/tasks/{task_id}/start` | 启动任务 |
| POST | `/tasks/{task_id}/pause` | 暂停任务 |
| POST | `/tasks/{task_id}/resume` | 继续任务 |
| GET | `/records/{record_id}/download/txt` | 下载 TXT |
| GET | `/records/{record_id}/download/docx` | 下载 DOCX |

## 数据存储

默认数据库：

```text
backend/pagestruct_ai.db
```

核心表：

- `task`：任务信息
- `parse_record`：每条 URL 的解析记录
- `attachment`：附件链接
- `upload_file`：上传文件信息

运行时文件目录：

```text
backend/storage/uploads/
backend/storage/txt/
backend/storage/docx/
```

## 核心处理流程

```text
用户提交 URL 或上传 CSV / XLSX
        ↓
创建 task 和 parse_record
        ↓
启动任务
        ↓
fetch_service 获取网页
        ↓
extract_service 提取正文和附件链接
        ↓
llm_service 标准化内容
        ↓
保存数据库
        ↓
docx_service 生成 TXT / DOCX
        ↓
页面展示和下载
```

## 开发约束

- 不让大模型直接访问网页。
- 不把 URL 直接交给大模型。
- HTTP 状态和网络错误由程序判断。
- LLM 只处理已经提取的正文和附件链接。
- LLM 必须输出严格 JSON。
- LLM 输出必须经过 Pydantic 校验。
- LLM 输出附件 URL 必须来自原始 `file_links`。
- 批量任务每条 URL 完成后立即保存。
- 暂停任务不强杀当前记录。
- 继续任务只处理未完成记录。

## 验证命令

```bash
cd backend
PYTHONPYCACHEPREFIX=/tmp/pagestruct_pycache .venv/bin/python -m compileall app
.venv/bin/python -c 'from app.main import app; print(app.title)'
curl http://127.0.0.1:8000/api/health
```

## 当前限制

- 批量任务目前是同步串行执行，后续可以升级为后台线程或任务队列。
- 没有用户登录和权限系统。
- 没有复杂反爬、验证码处理、浏览器渲染和 OCR。
- 没有 Alembic 数据库迁移系统。
- LLM 调用目前按 OpenAI-compatible Chat Completions 格式解析。
