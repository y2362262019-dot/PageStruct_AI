# PageStruct AI Backend

当前包含 PageStruct AI MVP 后端和 Jinja2 + HTMX 页面。

## 功能

- 单条 URL 任务创建和解析
- CSV / XLSX 批量上传
- 批量任务串行执行
- 批量任务暂停和继续
- SQLAlchemy + SQLite 数据持久化
- 网页获取、正文提取、附件链接提取
- LLM 标准化服务和 Pydantic 校验
- TXT / DOCX 导出下载

## 启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/api/health`

## 环境变量

项目启动时会自动读取：

```text
../.env
.env
```

如果两个文件都存在，`backend/.env` 中的同名配置优先。

创建本地配置：

```bash
cp .env.example .env
```

示例：

```env
LLM_API_KEY=your-api-key
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT=60
```

`LLM_API_KEY` 不配置时，系统仍可完成网页抓取、正文提取和文件导出，LLM 失败原因会保存到记录中。

## 常用页面

- `/` 首页，创建单条任务或上传批量文件
- `/tasks` 任务列表
- `/tasks/{task_id}` 任务详情和进度
- `/records/{record_id}` 解析记录详情
