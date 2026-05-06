# PageStruct AI

中文说明：[`README.zh-CN.md`](README.zh-CN.md)
English: [`README.en.md`](README.en.md)

PageStruct AI 是一个网页内容解析与归档基础设施项目。

> **注意：** LLM 集成和 Web 应用 (`backend/app/`) 已移除。五年规划文件爬虫已迁移至[独立仓库](https://github.com/y2362262019-dot/five_year_plan_crawler)。

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

## 项目结构

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

## 快速启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 数据存储

默认数据库：

```text
backend/pagestruct_ai.db
```

运行时文件目录：

```text
backend/storage/uploads/
backend/storage/txt/
backend/storage/docx/
```
