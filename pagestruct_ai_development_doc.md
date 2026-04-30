# PageStruct AI 开发文档与开发约束

> 前端方案：**Jinja2 + HTMX**  
> 后端方案：**Python + FastAPI + SQLAlchemy + SQLite**  
> 开发方式：分阶段、小步提交、每一步可运行、每一步可测试。

---

## 一、项目名称

**PageStruct AI**

---

## 二、项目介绍

**PageStruct AI** 是一个基于爬虫与大模型的网页内容标准化解析系统。

系统支持用户输入单条网页链接，或者上传 CSV / Excel 文件进行批量网页解析。系统会自动访问网页，判断网页是否有效，提取网页正文内容和文件链接，再将提取到的原始内容交给大模型进行标准化整理，最后将结构化结果保存到数据库，并通过网页端进行展示、预览和下载。

系统重点解决以下场景：

| 编号 | 网页情况 | 系统处理方式 |
|---|---|---|
| 1 | 页面打不开、404、超时 | 标记为页面无效，记录错误原因 |
| 2 | 页面能打开，但网页内容为空或无效 | 标记为内容为空或无效 |
| 3 | 页面只有文件链接，没有正文 | 提取文件链接，供用户查看和下载 |
| 4 | 页面只有正文，没有文件链接 | 提取正文，支持保存为 TXT / DOCX |
| 5 | 页面既有正文又有文件链接 | 同时提取正文与文件链接 |

---

## 三、项目核心定位

本项目不是单纯的爬虫系统，也不是简单的大模型问答系统，而是一个完整的：

```text
网页获取系统 + 内容解析系统 + 大模型标准化系统 + 任务管理系统 + 数据归档系统
```

核心流程如下：

```text
用户提交 URL / 上传 CSV 或 Excel
        ↓
创建解析任务
        ↓
程序访问网页并提取原始内容
        ↓
提取网页正文和文件链接
        ↓
将提取结果交给大模型标准化
        ↓
保存到数据库
        ↓
通过 Jinja2 + HTMX 页面展示
        ↓
支持 TXT / DOCX 下载
```

---

## 四、核心设计原则

### 1. 不让大模型直接负责抓网页

大模型只负责：

```text
理解文本
清洗内容
标准化输出
判断页面类型
生成摘要
整理附件信息
```

大模型不负责：

```text
访问网页
判断 HTTP 状态码
下载文件
写入数据库
控制任务暂停继续
管理批量任务进度
```

这些必须由后端程序完成。

---

### 2. 先程序规则，后大模型

系统流程必须是：

```text
URL
 ↓
程序访问网页
 ↓
程序提取原始 HTML / 原始文本 / 链接
 ↓
程序初步判断网页状态
 ↓
必要时调用大模型标准化
 ↓
保存数据库
 ↓
前端展示
```

不能一上来就把 URL 丢给大模型。

---

### 3. 大模型必须输出严格 JSON

禁止让大模型自由发挥文本。

错误方式：

```text
请帮我整理这个网页内容
```

正确方式：

```text
请严格按照以下 JSON Schema 输出，不要输出 Markdown，不要解释，不要编造输入中不存在的信息。
```

---

### 4. 所有解析步骤必须可追踪

每条 URL 解析记录都要保存：

```text
原始 URL
最终 URL
HTTP 状态码
网页标题
原始文本
提取到的链接
大模型标准化结果
解析状态
错误原因
创建时间
更新时间
```

这样即使大模型解析错误，也可以重新解析，不需要重新访问网页。

---

### 5. 每完成一条 URL 就立即保存

批量任务中不能等所有 URL 完成后再保存。

正确方式：

```text
解析一条
保存一条
更新进度
继续下一条
```

这样才能支持暂停、继续和异常恢复。

---

## 五、推荐技术栈

### 后端

```text
Python
FastAPI
SQLAlchemy
SQLite / 后期可切换 MySQL
requests
BeautifulSoup4
readability-lxml
python-docx
pandas
openpyxl
python-multipart
jinja2
```

### 前端

```text
Jinja2 模板
HTMX 局部刷新
少量原生 JavaScript
基础 CSS
```

### 第一版数据库

```text
SQLite
```

后续稳定后可切换为：

```text
MySQL
```

### 第一版任务处理

```text
FastAPI 后台任务 / Python ThreadPoolExecutor / 简单串行执行
```

后续再升级为：

```text
Redis + Celery
```

第一版不要一开始就上 Celery，否则调试成本会变高。

---

## 六、为什么前端使用 Jinja2 + HTMX

本项目第一版重点是后台解析逻辑，不需要复杂前端框架。

Jinja2 + HTMX 的优势是：

```text
1. 不需要 React / Vue 构建流程。
2. 后端渲染页面，开发速度快。
3. HTMX 可以实现局部刷新，适合任务进度更新。
4. 页面结构简单，方便 Codex 生成和维护。
5. 更适合后台管理类工具。
```

适合本项目的功能：

```text
任务列表自动刷新
任务详情局部刷新
解析进度轮询
暂停 / 继续按钮异步请求
记录详情页面展示
下载按钮
```

---

## 七、项目目录结构建议

```text
pagestruct-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── task.py
│   │   │   ├── parse_record.py
│   │   │   ├── attachment.py
│   │   │   └── upload_file.py
│   │   ├── schemas/
│   │   │   ├── task_schema.py
│   │   │   ├── record_schema.py
│   │   │   └── llm_schema.py
│   │   ├── services/
│   │   │   ├── fetch_service.py
│   │   │   ├── extract_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── task_service.py
│   │   │   ├── docx_service.py
│   │   │   └── file_service.py
│   │   ├── routers/
│   │   │   ├── page_router.py
│   │   │   ├── task_router.py
│   │   │   ├── record_router.py
│   │   │   ├── upload_router.py
│   │   │   └── download_router.py
│   │   ├── utils/
│   │   │   ├── url_utils.py
│   │   │   ├── text_utils.py
│   │   │   └── status_utils.py
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── tasks.html
│   │   │   ├── task_detail.html
│   │   │   ├── record_detail.html
│   │   │   └── partials/
│   │   │       ├── task_table.html
│   │   │       ├── task_progress.html
│   │   │       ├── record_table.html
│   │   │       └── flash_message.html
│   │   └── static/
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           └── app.js
│   ├── storage/
│   │   ├── uploads/
│   │   ├── txt/
│   │   └── docx/
│   ├── requirements.txt
│   └── README.md
└── README.md
```

---

## 八、系统核心流程

### 1. 单条 URL 解析流程

```text
用户输入 URL
 ↓
后端校验 URL 格式
 ↓
创建 task 任务
 ↓
创建 parse_record 记录
 ↓
状态设置为 PENDING
 ↓
开始解析
 ↓
状态设置为 PROCESSING
 ↓
请求网页
 ↓
判断 HTTP 状态
 ↓
提取标题、正文、链接、文件链接
 ↓
将提取结果交给大模型标准化
 ↓
保存标准化 JSON
 ↓
保存正文、附件列表
 ↓
生成 TXT / DOCX
 ↓
状态设置为 COMPLETED
 ↓
前端展示结果
```

---

### 2. 批量文件解析流程

```text
用户上传 CSV / Excel
 ↓
后端读取文件
 ↓
识别 URL 列
 ↓
创建 batch task
 ↓
为每个 URL 创建 parse_record
 ↓
逐条解析
 ↓
每条完成后保存结果
 ↓
更新 completed_count / failed_count
 ↓
HTMX 局部刷新进度
```

---

### 3. 暂停与继续流程

第一版建议采用稳定方案：

```text
用户点击暂停
 ↓
任务状态设置为 PAUSED
 ↓
当前正在解析的 URL 继续执行完成
 ↓
后续等待中的 URL 不再开始
```

继续逻辑：

```text
用户点击继续
 ↓
任务状态设置为 RUNNING
 ↓
系统查找该任务下 PENDING / FAILED 可重试记录
 ↓
继续逐条解析
```

第一版不要强制中断正在解析的 URL。强制中断容易造成状态混乱。

---

## 九、状态设计

### 1. 任务状态 task.status

```text
PENDING      等待中
RUNNING      运行中
PAUSED       已暂停
COMPLETED    已完成
FAILED       任务失败
CANCELED     已取消
```

---

### 2. 单条解析记录状态 parse_record.execute_status

```text
PENDING       等待解析
PROCESSING    正在解析
COMPLETED     解析完成
FAILED        解析失败
SKIPPED       已跳过
```

---

### 3. 页面获取状态 parse_record.fetch_status

```text
SUCCESS         获取成功
INVALID_URL     URL 格式错误
TIMEOUT         请求超时
HTTP_ERROR      HTTP 状态异常
NETWORK_ERROR   网络错误
SSL_ERROR       SSL 错误
UNKNOWN_ERROR   未知错误
```

---

### 4. 内容结果类型 parse_record.result_type

```text
INVALID_PAGE       页面无效
EMPTY_CONTENT      页面有效但内容为空
ONLY_FILES         只有文件链接
ONLY_TEXT          只有正文内容
TEXT_AND_FILES     正文和文件链接都有
FAILED             解析失败
```

---

## 十、数据库设计

### 1. task 表

用于保存单条任务或批量任务。

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | Integer | 主键 |
| task_name | String | 任务名称 |
| task_type | String | single / batch |
| status | String | 任务状态 |
| total_count | Integer | 总 URL 数 |
| completed_count | Integer | 已完成数量 |
| failed_count | Integer | 失败数量 |
| paused_at | DateTime | 暂停时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

### 2. parse_record 表

用于保存每条 URL 的解析结果。

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | Integer | 主键 |
| task_id | Integer | 所属任务 ID |
| url | Text | 原始 URL |
| final_url | Text | 重定向后的最终 URL |
| title | Text | 网页标题 |
| http_status | Integer | HTTP 状态码 |
| fetch_status | String | 页面获取状态 |
| execute_status | String | 执行状态 |
| result_type | String | 内容结果类型 |
| raw_text | Text | 程序提取的原始文本 |
| clean_text | Text | 清洗后的正文 |
| summary | Text | 大模型生成摘要 |
| fetch_json | JSON/Text | 原始抓取结果 |
| llm_json | JSON/Text | 大模型标准化结果 |
| error_message | Text | 错误信息 |
| txt_file_path | Text | TXT 文件路径 |
| docx_file_path | Text | DOCX 文件路径 |
| started_at | DateTime | 开始解析时间 |
| completed_at | DateTime | 完成时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

### 3. attachment 表

用于保存网页中的文件链接。

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | Integer | 主键 |
| record_id | Integer | 所属解析记录 ID |
| file_name | Text | 文件名 |
| file_type | String | 文件类型 |
| file_url | Text | 文件链接 |
| link_text | Text | 原始链接文字 |
| description | Text | 文件说明 |
| is_downloaded | Boolean | 是否已下载 |
| local_file_path | Text | 本地文件路径 |
| created_at | DateTime | 创建时间 |

---

### 4. upload_file 表

用于保存批量上传文件信息。

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | Integer | 主键 |
| task_id | Integer | 所属任务 |
| original_filename | Text | 原始文件名 |
| file_path | Text | 保存路径 |
| file_type | String | csv / xlsx |
| url_column | String | URL 所在列 |
| total_rows | Integer | 总行数 |
| created_at | DateTime | 创建时间 |

---

## 十一、网页获取层设计

### fetch_service.py 负责内容

```text
1. 校验 URL 格式
2. 请求网页
3. 处理超时
4. 处理状态码
5. 处理重定向
6. 返回 HTML、状态码、最终 URL
```

### 返回结构

```json
{
  "url": "https://example.com/a.html",
  "final_url": "https://example.com/a.html",
  "fetch_status": "SUCCESS",
  "http_status": 200,
  "html": "<html>...</html>",
  "error_message": null
}
```

### 约束

```text
请求超时时间默认 15 秒
不自动无限重试
最多重试 1 次
必须设置 User-Agent
禁止抓取非 http / https 链接
发生异常不能让程序崩溃，必须返回结构化错误
```

---

## 十二、内容提取层设计

### extract_service.py 负责内容

```text
1. 从 HTML 中提取网页标题
2. 提取正文文本
3. 提取所有 a 标签链接
4. 补全相对链接
5. 判断疑似文件链接
6. 清洗多余空白
```

### 文件链接判断规则

优先根据文件后缀判断：

```text
.pdf
.doc
.docx
.xls
.xlsx
.ppt
.pptx
.zip
.rar
.txt
.csv
```

同时根据链接文字判断：

```text
下载
附件
点击下载
文件
正文
PDF
Word
Excel
申报表
名单
通知书
附件1
附件2
```

### 返回结构

```json
{
  "title": "网页标题",
  "raw_text": "原始正文文本",
  "clean_text": "清洗后的正文文本",
  "links": [
    {
      "text": "首页",
      "url": "https://example.com"
    }
  ],
  "file_links": [
    {
      "text": "附件1：申报表.docx",
      "url": "https://example.com/files/a.docx",
      "file_name": "附件1：申报表.docx",
      "file_type": "docx"
    }
  ]
}
```

---

## 十三、大模型标准化层设计

### 1. 大模型输入

大模型不能直接输入完整 HTML。

应该输入：

```json
{
  "source_url": "https://example.com/page.html",
  "html_title": "网页标题",
  "clean_text": "程序提取后的正文",
  "file_links": [
    {
      "text": "附件1：申报表.docx",
      "url": "https://example.com/files/a.docx",
      "file_name": "附件1：申报表.docx",
      "file_type": "docx"
    }
  ]
}
```

---

### 2. 大模型输出 JSON

大模型必须输出以下结构：

```json
{
  "result_type": "TEXT_AND_FILES",
  "is_valid": true,
  "title": "关于某某事项的通知",
  "summary": "本文主要说明某某事项的申报要求、时间安排和附件材料。",
  "main_content": "正文内容...",
  "content_sections": [
    {
      "heading": "一、申报对象",
      "content": "相关正文内容..."
    },
    {
      "heading": "二、申报时间",
      "content": "相关正文内容..."
    }
  ],
  "attachments": [
    {
      "name": "附件1：申报表.docx",
      "type": "docx",
      "url": "https://example.com/files/a.docx",
      "description": "申报表文件"
    }
  ],
  "invalid_reason": null,
  "confidence": 0.92
}
```

---

### 3. result_type 只能从以下值中选择

```text
INVALID_PAGE
EMPTY_CONTENT
ONLY_FILES
ONLY_TEXT
TEXT_AND_FILES
FAILED
```

---

### 4. 大模型提示词约束

可以使用下面这个提示词作为第一版基础。

```text
你是一个网页内容标准化解析助手。

我会提供一个网页的标题、正文文本和文件链接列表。
你的任务是根据输入内容，判断网页内容类型，并输出标准化 JSON。

你必须遵守以下规则：

1. 只能根据输入内容进行整理，不允许编造输入中不存在的信息。
2. 附件 URL 必须来自输入的 file_links，不能自己生成 URL。
3. 如果没有正文内容，main_content 必须为空字符串。
4. 如果没有附件，attachments 必须为空数组。
5. 如果网页正文为空但存在附件，result_type 应为 ONLY_FILES。
6. 如果网页有正文但没有附件，result_type 应为 ONLY_TEXT。
7. 如果网页既有正文又有附件，result_type 应为 TEXT_AND_FILES。
8. 如果正文和附件都为空，result_type 应为 EMPTY_CONTENT。
9. 如果页面明显无效，result_type 应为 INVALID_PAGE。
10. 不要输出 Markdown。
11. 不要输出解释文字。
12. 必须输出合法 JSON。

请严格按照以下 JSON 格式输出：

{
  "result_type": "",
  "is_valid": true,
  "title": "",
  "summary": "",
  "main_content": "",
  "content_sections": [
    {
      "heading": "",
      "content": ""
    }
  ],
  "attachments": [
    {
      "name": "",
      "type": "",
      "url": "",
      "description": ""
    }
  ],
  "invalid_reason": null,
  "confidence": 0.0
}
```

---

## 十四、减少大模型幻觉的约束

### 1. 不允许大模型生成新链接

大模型输出的附件链接必须来自输入。

后端要做校验：

```text
如果大模型输出的附件 URL 不在原始 file_links 中，则丢弃该附件。
```

---

### 2. 不允许大模型编造发布时间

如果网页获取层没有提取到发布时间，大模型输出不能乱写。

建议第一版不做 publish_date，后期再加。

---

### 3. 大模型输出必须经过 JSON 解析校验

流程：

```text
调用大模型
 ↓
尝试 json.loads()
 ↓
如果失败，进行一次修复调用
 ↓
如果仍失败，记录 LLM_PARSE_ERROR
```

不能直接相信大模型返回内容。

---

### 4. 大模型内容不能覆盖程序状态

例如：

```text
HTTP 404
```

这种情况下，后端已经判断页面无效，不需要再调用大模型。

程序判断优先级高于大模型。

---

### 5. 使用 Pydantic Schema 校验输出

后端应定义一个 `LLMResult` 模型：

```python
class LLMResult(BaseModel):
    result_type: Literal[
        "INVALID_PAGE",
        "EMPTY_CONTENT",
        "ONLY_FILES",
        "ONLY_TEXT",
        "TEXT_AND_FILES",
        "FAILED"
    ]
    is_valid: bool
    title: str = ""
    summary: str = ""
    main_content: str = ""
    content_sections: list[ContentSection] = []
    attachments: list[AttachmentResult] = []
    invalid_reason: str | None = None
    confidence: float = 0.0
```

---

## 十五、文档导出设计

### 1. TXT 文件内容格式

```text
标题：xxx

来源链接：xxx
解析时间：2026-04-30 10:20:00

一、网页正文

正文第一段……
正文第二段……

二、文件链接

1. 附件1：xxx.docx
   类型：docx
   链接：https://example.com/a.docx

2. 附件2：xxx.pdf
   类型：pdf
   链接：https://example.com/b.pdf
```

---

### 2. DOCX 文件内容格式

DOCX 需要注意排版：

```text
标题：加粗，居中
来源链接：普通段落
解析时间：普通段落
一级标题：网页正文
正文：按段落保存
一级标题：文件链接
文件链接：使用表格展示
```

文件链接表格字段：

| 序号 | 文件名 | 类型 | 下载链接 |
|---|---|---|---|

---

## 十六、Jinja2 + HTMX 前端页面设计

### 1. base.html

基础模板包含：

```text
页面标题
导航栏
主内容块
HTMX CDN
全局 CSS
少量全局 JS
```

建议导航：

```text
首页
任务列表
```

---

### 2. 首页 index.html

功能：

```text
输入单条 URL
上传 CSV / Excel
填写 URL 所在列名
点击创建任务
```

页面表单建议：

```html
<form hx-post="/tasks/single" hx-target="#message" hx-swap="innerHTML">
  <input type="url" name="url" placeholder="请输入网页链接" required>
  <button type="submit">创建单条解析任务</button>
</form>

<div id="message"></div>
```

批量上传建议：

```html
<form hx-post="/tasks/batch/upload" hx-target="#message" hx-swap="innerHTML" enctype="multipart/form-data">
  <input type="file" name="file" accept=".csv,.xlsx" required>
  <input type="text" name="url_column" placeholder="URL 列名，例如：网页链接" required>
  <button type="submit">上传并创建批量任务</button>
</form>
```

---

### 3. 任务列表页 tasks.html

展示字段：

| 任务名称 | 类型 | 状态 | 总数 | 已完成 | 失败 | 创建时间 | 操作 |
|---|---|---|---:|---:|---:|---|---|

HTMX 设计：

```html
<div id="task-table"
     hx-get="/tasks/partials/table"
     hx-trigger="load, every 3s"
     hx-swap="innerHTML">
</div>
```

这样任务列表可以每 3 秒自动刷新。

---

### 4. 任务详情页 task_detail.html

展示每条 URL 的解析状态：

| 序号 | URL | 标题 | 执行状态 | 结果类型 | 文件数 | 操作 |
|---|---|---|---|---|---:|---|

规则：

```text
PROCESSING 状态不能点击查看
PENDING 状态不能点击查看
COMPLETED 可以查看详情
FAILED 可以查看错误信息
```

HTMX 局部刷新任务进度：

```html
<div id="task-progress"
     hx-get="/tasks/{{ task.id }}/partials/progress"
     hx-trigger="load, every 2s"
     hx-swap="innerHTML">
</div>

<div id="record-table"
     hx-get="/tasks/{{ task.id }}/partials/records"
     hx-trigger="load, every 3s"
     hx-swap="innerHTML">
</div>
```

---

### 5. 记录详情页 record_detail.html

展示内容：

```text
原始 URL
最终 URL
网页标题
解析状态
结果类型
摘要
正文内容
附件列表
下载 TXT
下载 DOCX
```

附件列表：

| 序号 | 文件名 | 类型 | 下载链接 |
|---|---|---|---|

---

### 6. partials 局部模板

建议使用以下局部模板：

```text
templates/partials/task_table.html
templates/partials/task_progress.html
templates/partials/record_table.html
templates/partials/flash_message.html
```

这些模板专门给 HTMX 局部刷新使用。

---

## 十七、接口与页面路由设计

本项目使用 Jinja2 + HTMX，因此需要同时设计“页面路由”和“动作路由”。

---

### 1. 页面路由

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 首页 |
| GET | `/tasks` | 任务列表页 |
| GET | `/tasks/{task_id}` | 任务详情页 |
| GET | `/records/{record_id}` | 记录详情页 |

---

### 2. HTMX 局部刷新路由

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/tasks/partials/table` | 返回任务表格局部 HTML |
| GET | `/tasks/{task_id}/partials/progress` | 返回任务进度局部 HTML |
| GET | `/tasks/{task_id}/partials/records` | 返回任务下记录表格局部 HTML |

---

### 3. 动作路由

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/tasks/single` | 创建单条解析任务 |
| POST | `/tasks/batch/upload` | 上传 CSV / Excel 并创建批量任务 |
| POST | `/tasks/{task_id}/start` | 启动任务 |
| POST | `/tasks/{task_id}/pause` | 暂停任务 |
| POST | `/tasks/{task_id}/resume` | 继续任务 |
| GET | `/records/{record_id}/download/txt` | 下载 TXT |
| GET | `/records/{record_id}/download/docx` | 下载 DOCX |

---

### 4. 可选 JSON API 路由

后期如果需要前后端分离，可以保留 `/api` 前缀接口。

第一版使用 Jinja2 + HTMX 时，不强制要求做完整 JSON API。

---

## 十八、HTMX 使用约束

### 1. HTMX 只负责页面交互，不负责业务逻辑

业务逻辑必须在后端 service 中完成。

HTMX 只做：

```text
提交表单
局部刷新
轮询进度
替换 HTML 片段
```

---

### 2. 复杂状态不要放在前端

任务状态必须来自数据库。

不要在前端自己维护：

```text
任务是否运行
完成数量
失败数量
记录是否可查看
```

这些都必须由后端查询数据库后渲染。

---

### 3. PROCESSING / PENDING 记录不能查看

后端渲染按钮时要判断状态：

```jinja2
{% if record.execute_status == "COMPLETED" or record.execute_status == "FAILED" %}
  <a href="/records/{{ record.id }}">查看</a>
{% else %}
  <button disabled>解析中，暂不可查看</button>
{% endif %}
```

---

### 4. 轮询频率不要太高

建议：

```text
任务进度：每 2 秒刷新一次
任务列表：每 3 到 5 秒刷新一次
记录表格：每 3 秒刷新一次
```

不要设置 0.5 秒之类的高频刷新。

---

## 十九、开发阶段规划

下面是给 Codex 使用时最重要的部分。开发必须严格按照阶段进行，不要一次性生成整个项目。

---

## 第 0 阶段：创建项目骨架

### 目标

只创建项目结构，不实现复杂功能。

### 要完成

```text
1. 创建 backend 目录
2. 创建 FastAPI 项目
3. 配置 Jinja2Templates
4. 配置 StaticFiles
5. 创建基础模板 base.html
6. 创建首页 index.html
7. 创建健康检查接口
8. 创建 requirements.txt
```

### 验收标准

```text
运行 uvicorn app.main:app --reload 后可以访问：
/ 页面
/api/health 接口
```

### 给 Codex 的提示词

```text
请创建 PageStruct AI 项目的 backend 基础结构。

要求：
1. 使用 FastAPI。
2. 使用 Jinja2Templates。
3. 使用 StaticFiles 挂载 static 目录。
4. 创建 app/main.py、app/config.py、app/database.py。
5. 创建 templates/base.html 和 templates/index.html。
6. 创建 static/css/style.css。
7. 添加健康检查接口 GET /api/health。
8. 首页 GET / 使用 Jinja2 渲染。
9. 暂时不要实现爬虫，不要实现大模型，不要实现数据库模型。
10. 只完成项目骨架，确保可以运行。
11. 给出 requirements.txt 和启动命令。
```

---

## 第 1 阶段：数据库模型

### 目标

建立数据库表结构。

### 要完成

```text
1. Task 模型
2. ParseRecord 模型
3. Attachment 模型
4. UploadFile 模型
5. 自动创建数据库表
```

### 验收标准

```text
启动后自动生成 SQLite 数据库
数据库中存在四张表
/api/health 正常
```

### 给 Codex 的提示词

```text
在现有 FastAPI 项目中添加数据库模型。

要求：
1. 使用 SQLAlchemy ORM。
2. 创建 Task、ParseRecord、Attachment、UploadFile 四个模型。
3. 字段按照开发文档设计。
4. 添加 created_at、updated_at 字段。
5. 启动项目时自动创建表。
6. 不要写爬虫逻辑。
7. 不要写大模型逻辑。
8. 不要写复杂页面。
9. 保持代码简单清晰。
```

---

## 第 2 阶段：单条 URL 任务创建

### 目标

用户在首页输入 URL 后，系统能创建任务和解析记录。

### 要完成

```text
1. POST /tasks/single
2. 校验 URL 基础格式
3. 创建 task
4. 创建 parse_record
5. 返回 HTMX 局部提示信息
```

### 验收标准

```text
在首页输入 URL 并提交后，页面显示创建成功
数据库中新增一条 task 和一条 parse_record
```

### 给 Codex 的提示词

```text
请在现有项目中实现单条 URL 任务创建功能。

要求：
1. 首页 index.html 添加 URL 输入表单。
2. 表单使用 HTMX：hx-post="/tasks/single"，hx-target="#message"。
3. 后端新增 POST /tasks/single。
4. 请求参数从 Form 中读取 url。
5. 校验 url 必须以 http:// 或 https:// 开头。
6. 创建 Task，task_type 为 single，status 为 PENDING，total_count 为 1。
7. 创建 ParseRecord，execute_status 为 PENDING。
8. 返回一段 HTML 片段，提示创建成功，并提供任务详情页链接。
9. 不要立即解析网页。
10. 不要调用大模型。
```

---

## 第 3 阶段：任务列表和任务详情页面

### 目标

能通过 Jinja2 页面查看任务和记录。

### 要完成

```text
1. GET /tasks
2. GET /tasks/{task_id}
3. templates/tasks.html
4. templates/task_detail.html
5. partials/task_table.html
6. partials/record_table.html
```

### 验收标准

```text
可以在任务列表页看到已创建任务
可以进入任务详情页看到 URL 记录
```

### 给 Codex 的提示词

```text
请实现任务列表页和任务详情页。

要求：
1. GET /tasks 渲染 templates/tasks.html。
2. GET /tasks/{task_id} 渲染 templates/task_detail.html。
3. tasks.html 展示任务名称、类型、状态、总数、完成数、失败数、创建时间、操作。
4. task_detail.html 展示该任务下所有 parse_record。
5. 创建 templates/partials/task_table.html 和 templates/partials/record_table.html。
6. tasks.html 中使用 HTMX 每 3 秒刷新任务表格。
7. task_detail.html 中使用 HTMX 每 3 秒刷新记录表格。
8. 不要实现爬虫。
9. 不要调用大模型。
```

---

## 第 4 阶段：网页获取服务

### 目标

实现最基础的网页访问能力。

### 要完成

```text
1. fetch_page(url)
2. 返回状态码
3. 返回 HTML
4. 处理超时
5. 处理异常
```

### 验收标准

```text
给一个正常 URL，可以返回 SUCCESS
给一个错误 URL，可以返回结构化错误
```

### 给 Codex 的提示词

```text
请实现 fetch_service.py。

要求：
1. 使用 requests 获取网页。
2. 设置 User-Agent。
3. 超时时间为 15 秒。
4. 只允许 http 和 https URL。
5. 返回统一字典结构：
   {
     "fetch_status": "",
     "http_status": null,
     "final_url": "",
     "html": "",
     "error_message": null
   }
6. 对 timeout、网络错误、SSL 错误、HTTP 状态异常分别处理。
7. 不要让异常抛出导致程序崩溃。
8. 不要提取正文。
9. 不要调用大模型。
```

---

## 第 5 阶段：正文和链接提取服务

### 目标

从 HTML 中提取标题、正文、所有链接、文件链接。

### 要完成

```text
1. extract_title()
2. extract_text()
3. extract_links()
4. extract_file_links()
5. 补全相对链接
```

### 验收标准

```text
输入 HTML 和 base_url，能够返回标题、正文、链接数组、文件链接数组
```

### 给 Codex 的提示词

```text
请实现 extract_service.py。

要求：
1. 使用 BeautifulSoup 解析 HTML。
2. 提取 title 标签作为标题。
3. 删除 script、style、noscript 标签。
4. 提取正文文本，保留基本换行。
5. 提取所有 a 标签链接。
6. 使用 urljoin 补全相对链接。
7. 根据文件后缀和链接文字识别文件链接。
8. 文件类型包括 pdf、doc、docx、xls、xlsx、ppt、pptx、zip、rar、txt、csv。
9. 返回统一结构：
   {
     "title": "",
     "raw_text": "",
     "clean_text": "",
     "links": [],
     "file_links": []
   }
10. 不要调用大模型。
11. 不要保存数据库。
```

---

## 第 6 阶段：单条 URL 完整解析流程

### 目标

把任务创建、网页获取、内容提取串起来。

### 要完成

```text
1. POST /tasks/{task_id}/start
2. 查找该任务下的 parse_record
3. 执行 fetch_page
4. 执行 extract_service
5. 保存 raw_text、clean_text、fetch_json
6. 根据规则初步判断 result_type
7. 更新状态
8. HTMX 返回启动提示
```

### 第一版 result_type 规则

```text
网页请求失败 → INVALID_PAGE
正文为空且文件链接为空 → EMPTY_CONTENT
正文为空且文件链接不为空 → ONLY_FILES
正文不为空且文件链接为空 → ONLY_TEXT
正文不为空且文件链接不为空 → TEXT_AND_FILES
```

### 验收标准

```text
任务详情页点击“开始解析”后，可以解析并保存结果
任务详情页通过 HTMX 自动刷新状态
```

### 给 Codex 的提示词

```text
请实现单条任务启动解析功能。

要求：
1. 新增 POST /tasks/{task_id}/start。
2. task_detail.html 添加“开始解析”按钮，使用 HTMX 提交。
3. 只处理 single 类型任务。
4. 将 task.status 设置为 RUNNING。
5. 将 parse_record.execute_status 设置为 PROCESSING。
6. 调用 fetch_page 获取网页。
7. 如果获取失败，保存错误信息，record 设置为 FAILED，result_type 设置为 INVALID_PAGE。
8. 如果获取成功，调用 extract_service 提取标题、正文和文件链接。
9. 根据正文和文件链接数量判断 result_type。
10. 保存 raw_text、clean_text、fetch_json。
11. 保存附件链接到 attachment 表。
12. 更新 task 的 completed_count 或 failed_count。
13. 不要调用大模型。
14. 确保每一步异常都能被捕获并写入 error_message。
15. 返回 HTMX HTML 片段，提示任务已启动或已完成。
```

---

## 第 7 阶段：记录详情页

### 目标

解析完成后可以查看具体结果。

### 要完成

```text
1. GET /records/{record_id}
2. record_detail.html
3. 展示正文和附件列表
4. 未完成状态禁止查看或提示不可查看
```

### 验收标准

```text
COMPLETED 记录可以查看详情
PROCESSING / PENDING 记录不能查看详情
```

### 给 Codex 的提示词

```text
请实现记录详情页。

要求：
1. GET /records/{record_id} 渲染 record_detail.html。
2. 如果记录状态是 PENDING 或 PROCESSING，页面提示“该记录尚未解析完成，暂不能查看”。
3. 如果记录状态是 COMPLETED 或 FAILED，展示详情。
4. 展示字段包括：原始 URL、最终 URL、标题、HTTP 状态、获取状态、执行状态、结果类型、错误信息、正文内容。
5. 展示附件列表，包括文件名、类型、链接文字、下载链接。
6. 不要实现 TXT / DOCX 下载。
7. 不要调用大模型。
```

---

## 第 8 阶段：大模型标准化服务

### 目标

将已经提取的正文和附件链接交给大模型，返回标准 JSON。

### 要完成

```text
1. llm_service.py
2. 构造 Prompt
3. 调用大模型
4. 解析 JSON
5. Pydantic 校验
6. 错误兜底
```

### 验收标准

```text
输入 clean_text 和 file_links，能返回合法的标准化 JSON
```

### 给 Codex 的提示词

```text
请实现 llm_service.py。

要求：
1. 创建 standardize_page_content(input_data) 函数。
2. input_data 包含 source_url、html_title、clean_text、file_links。
3. 使用环境变量读取大模型 API Key。
4. 大模型必须输出严格 JSON。
5. 使用 Pydantic 定义 LLMResult、ContentSection、AttachmentResult。
6. 对大模型返回内容执行 json.loads。
7. 如果 JSON 解析失败，返回 FAILED 类型，不要让程序崩溃。
8. 校验 attachments 中的 url 必须来自输入 file_links，否则丢弃。
9. 不允许大模型编造不存在的附件链接。
10. 暂时不要修改已有解析流程，只实现服务函数。
```

---

## 第 9 阶段：接入大模型标准化

### 目标

在网页解析成功后调用大模型，保存标准化结果。

### 要完成

```text
1. 解析成功后调用 llm_service
2. 保存 llm_json
3. 保存 summary
4. 保存 main_content
5. 根据大模型结果更新 result_type
```

### 约束

程序判断优先于大模型：

```text
如果 fetch 失败，不调用大模型
如果 HTTP 状态异常，不调用大模型
如果正文和文件链接都为空，可以不调用大模型
```

### 验收标准

```text
解析完成后，数据库中有 llm_json、summary、main_content
记录详情页能显示标准化摘要和正文
```

### 给 Codex 的提示词

```text
请将 llm_service 接入单条解析流程。

要求：
1. 只有 fetch_status 为 SUCCESS 时才允许调用大模型。
2. 如果 clean_text 为空且 file_links 为空，不调用大模型，直接标记 EMPTY_CONTENT。
3. 调用 standardize_page_content。
4. 保存 llm_json、summary、main_content。
5. 大模型返回失败时，不影响原始解析结果保存。
6. 程序原始提取到的附件链接仍然要保存。
7. result_type 可以使用大模型返回值，但必须限定在允许枚举内。
8. 所有异常必须写入 error_message。
9. record_detail.html 显示 summary 和 main_content。
```

---

## 第 10 阶段：TXT 和 DOCX 导出

### 目标

解析完成后生成可下载文件。

### 要完成

```text
1. generate_txt(record)
2. generate_docx(record)
3. 保存文件路径
4. 下载路由
5. 详情页显示下载按钮
```

### 验收标准

```text
已完成记录可以下载 TXT 和 DOCX
```

### 给 Codex 的提示词

```text
请实现 TXT 和 DOCX 导出功能。

要求：
1. 新建 docx_service.py。
2. 使用 python-docx 生成 DOCX。
3. TXT 和 DOCX 都包含标题、来源链接、解析时间、正文内容、文件链接列表。
4. DOCX 标题加粗居中。
5. 文件链接用表格展示。
6. 文件保存到 backend/storage/txt 和 backend/storage/docx。
7. 在 parse_record 中保存 txt_file_path 和 docx_file_path。
8. 新增下载路由：
   GET /records/{record_id}/download/txt
   GET /records/{record_id}/download/docx
9. 只有 COMPLETED 状态可以下载。
10. record_detail.html 中添加下载按钮。
```

---

## 第 11 阶段：批量上传 CSV / Excel

### 目标

支持用户上传文件并创建批量任务。

### 要完成

```text
1. 上传 CSV / Excel
2. 读取 URL 列
3. 创建 batch task
4. 创建多条 parse_record
5. 首页展示批量上传表单
```

### 验收标准

```text
上传文件后，数据库中生成一个 batch task 和多条 parse_record
页面提示创建成功，并提供任务详情链接
```

### 给 Codex 的提示词

```text
请实现批量上传功能。

要求：
1. 首页添加批量上传表单。
2. 表单使用 HTMX，提交到 POST /tasks/batch/upload。
3. 支持 csv、xlsx。
4. 使用 pandas 读取文件。
5. 请求参数包含 url_column。
6. 如果 url_column 不存在，返回 HTML 错误提示。
7. 只保留 http:// 或 https:// 开头的 URL。
8. 创建 task，task_type 为 batch。
9. 为每个 URL 创建 parse_record，状态为 PENDING。
10. 保存上传文件信息到 upload_file 表。
11. 不要立即解析。
```

---

## 第 12 阶段：批量任务执行

### 目标

批量任务可以逐条执行。

### 要完成

```text
1. start batch task
2. 按顺序解析 PENDING 记录
3. 每条解析完立即保存
4. 更新进度
5. HTMX 自动刷新任务详情页
```

### 验收标准

```text
批量任务可以从第一条解析到最后一条
任务进度持续更新
```

### 给 Codex 的提示词

```text
请实现批量任务执行逻辑。

要求：
1. POST /tasks/{task_id}/start 支持 batch 类型。
2. 查询该 task 下 execute_status 为 PENDING 的记录。
3. 按 id 顺序逐条解析。
4. 每解析一条就立即提交数据库。
5. 每条记录复用单条解析逻辑，避免重复代码。
6. 更新 task.completed_count 和 task.failed_count。
7. 全部完成后 task.status 设置为 COMPLETED。
8. 中途单条失败不能中断整个批量任务。
9. 不要并发，第一版先串行执行。
10. task_detail.html 中用 HTMX 每 2 到 3 秒刷新进度和记录表格。
```

---

## 第 13 阶段：暂停和继续任务

### 目标

支持任务暂停和继续。

### 要完成

```text
1. pause task
2. resume task
3. 批量解析过程中检测 task.status
4. HTMX 按钮局部刷新
```

### 验收标准

```text
用户点击暂停后，当前 URL 完成，后续 URL 不再执行
点击继续后，从未完成 URL 继续
```

### 给 Codex 的提示词

```text
请实现任务暂停和继续功能。

要求：
1. 新增 POST /tasks/{task_id}/pause。
2. 新增 POST /tasks/{task_id}/resume。
3. pause 时将 task.status 设置为 PAUSED。
4. 批量任务每解析完一条记录后，重新查询 task.status。
5. 如果发现 task.status 为 PAUSED，则停止继续解析。
6. resume 时将 task.status 设置为 RUNNING，并继续解析 PENDING 记录。
7. 不要强制中断正在 PROCESSING 的记录。
8. 保证暂停继续不会重复解析已经 COMPLETED 的记录。
9. task_detail.html 中根据状态显示开始、暂停、继续按钮。
10. 按钮使用 HTMX 提交并局部刷新提示信息。
```

---

## 第二十、开发约束总表

### 1. 代码约束

| 约束 | 要求 |
|---|---|
| 单一职责 | 每个 service 只做一类事情 |
| 不能跨层调用 | router 不直接写复杂业务 |
| 错误必须捕获 | 任何网页解析异常不能导致服务崩溃 |
| 状态必须保存 | 每条 URL 的状态都要入库 |
| 不重复代码 | 单条和批量解析复用同一个 record 解析函数 |
| 不一次性做太多 | 每阶段开发完成后先测试 |

---

### 2. 大模型约束

| 约束 | 要求 |
|---|---|
| 不直接访问网页 | 大模型只处理已提取内容 |
| 必须 JSON 输出 | 不允许 Markdown 和解释文字 |
| 必须 Schema 校验 | 使用 Pydantic 校验 |
| 不允许编造链接 | 附件 URL 必须来自输入 |
| 不覆盖程序错误 | HTTP 错误由程序判断 |
| 失败可降级 | LLM 失败不影响原始数据保存 |

---

### 3. 任务约束

| 约束 | 要求 |
|---|---|
| 每条 URL 独立记录 | 批量任务不能只存总结果 |
| 每条完成立即提交 | 支持断点继续 |
| 暂停不强杀当前记录 | 当前 URL 完成后暂停 |
| 继续只处理未完成记录 | 不重复处理 completed |
| 单条失败不影响批量 | 失败记录单独保存 |

---

### 4. 文件约束

| 约束 | 要求 |
|---|---|
| 上传文件限制格式 | 只支持 csv、xlsx |
| 下载文件安全 | 只能下载系统生成的 txt/docx |
| 文件名安全处理 | 去除特殊字符 |
| 附件第一版不自动下载 | 只展示原始链接 |
| DOCX 保持基本排版 | 标题、正文、附件表格 |

---

### 5. Jinja2 + HTMX 约束

| 约束 | 要求 |
|---|---|
| 页面渲染由后端完成 | Jinja2 负责完整页面和局部模板 |
| HTMX 不写业务逻辑 | 只负责提交、刷新、替换 HTML |
| 任务状态来自数据库 | 前端不自行维护任务状态 |
| 局部刷新要克制 | 2 到 5 秒刷新一次 |
| 未完成记录不可查看 | 后端渲染时控制按钮状态 |

---

## 第二十一、第一版不要做的功能

为了减少 bug，第一版不要做：

```text
1. 用户登录注册
2. 权限系统
3. 自动登录第三方网站
4. 验证码处理
5. 复杂反爬绕过
6. 多线程高并发解析
7. 附件自动批量下载
8. 网页截图
9. OCR
10. 图片内容理解
11. 表格复杂还原
12. 分布式任务队列
13. Redis + Celery
14. 多租户系统
15. React / Vue 前后端分离
```

这些可以放到第二版、第三版。

---

## 第二十二、推荐开发顺序总结

必须按照下面顺序来：

```text
第 0 阶段：项目骨架 + Jinja2 基础页面
第 1 阶段：数据库模型
第 2 阶段：单条 URL 创建任务
第 3 阶段：任务列表和任务详情页面
第 4 阶段：网页获取服务
第 5 阶段：正文和链接提取服务
第 6 阶段：单条 URL 完整解析
第 7 阶段：记录详情页
第 8 阶段：大模型标准化服务
第 9 阶段：接入大模型
第 10 阶段：TXT / DOCX 导出
第 11 阶段：批量上传
第 12 阶段：批量执行
第 13 阶段：暂停和继续
```

不要跳过前面的阶段。  
不要一开始就做大模型。  
不要一开始就做批量任务。  
先把单条 URL 的完整闭环跑通。

---

## 第二十三、最小可用版本 MVP 标准

当系统具备以下能力时，第一版就算完成：

```text
1. 用户可以输入单条 URL。
2. 系统可以创建解析任务。
3. 系统可以访问网页。
4. 系统可以判断网页是否有效。
5. 系统可以提取正文和文件链接。
6. 系统可以调用大模型标准化正文。
7. 系统可以保存结果到数据库。
8. 用户可以在 Jinja2 页面上查看解析结果。
9. 页面可以通过 HTMX 自动刷新任务进度。
10. 用户可以下载 TXT / DOCX。
11. 用户可以上传 CSV / Excel。
12. 系统可以批量解析 URL。
13. 用户可以查看批量任务进度。
14. 用户可以暂停和继续任务。
```

---

## 第二十四、给 Codex 的总提示词

你可以在开始开发前，把下面这段作为项目总提示词交给 Codex。

```text
我要开发一个名为 PageStruct AI 的网页内容解析系统。

项目目标：
用户可以输入单条 URL，也可以上传 CSV / Excel 文件进行批量 URL 解析。系统需要访问网页，判断网页是否有效，提取网页正文和文件链接，再调用大模型将内容标准化为 JSON，最后保存到数据库，并通过 Jinja2 + HTMX 页面展示结果，支持 TXT / DOCX 下载，支持批量任务暂停和继续。

核心原则：
1. 不要一次性完成所有功能。
2. 必须按照阶段逐步开发。
3. 每个阶段完成后都要保证项目可运行。
4. 前端使用 Jinja2 + HTMX，不使用 React，不使用 Vue。
5. 大模型不能直接访问网页。
6. 大模型只负责标准化已经提取的正文和文件链接。
7. 大模型必须输出严格 JSON。
8. 后端必须使用 Pydantic 校验大模型输出。
9. 后端必须防止大模型编造附件链接。
10. 网页获取、正文提取、链接提取、任务管理、数据库保存必须由程序完成。
11. 每条 URL 解析完成后必须立即保存状态。
12. 批量任务支持暂停和继续。
13. 第一版不要做登录、权限、验证码、反爬、多线程高并发、附件自动下载。

技术栈：
后端使用 Python + FastAPI + SQLAlchemy + SQLite。
前端使用 Jinja2 + HTMX。
网页获取使用 requests。
HTML 解析使用 BeautifulSoup。
文档导出使用 python-docx。
批量文件读取使用 pandas 和 openpyxl。
第一版先使用 SQLite，后续再迁移 MySQL。
第一版批量任务先串行执行，不要并发。

请从第 0 阶段开始，只创建项目骨架，不要跨阶段开发。
```

---

## 第二十五、最终开发提醒

这个项目一定要遵守一句话：

> **先让系统能稳定处理一条 URL，再让它处理很多 URL；先让程序能提取，再让大模型去整理；先让数据能保存，再让页面去展示。**

采用 Jinja2 + HTMX 时，尤其要注意：

```text
页面只是展示状态，状态必须来自数据库。
HTMX 只是局部刷新，不承担业务逻辑。
所有核心逻辑都必须放在后端 service 层。
```

这样开发最稳，也最能发挥大模型的优势。
