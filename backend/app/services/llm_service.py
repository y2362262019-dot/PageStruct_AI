from __future__ import annotations

import json
from typing import Any, Iterable

import requests
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.llm_schema import AttachmentResult, LLMResult


SYSTEM_PROMPT = """你是一个网页内容标准化解析助手。

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
"""


def _failed_result(reason: str) -> LLMResult:
    return LLMResult(
        result_type="FAILED",
        is_valid=False,
        invalid_reason=reason,
        confidence=0.0,
    )


def _allowed_attachment_urls(file_links: Iterable[dict[str, Any]]) -> set[str]:
    return {str(item.get("url", "")).strip() for item in file_links if item.get("url")}


def _sanitize_attachments(result: LLMResult, allowed_urls: set[str]) -> LLMResult:
    safe_attachments: list[AttachmentResult] = []
    for attachment in result.attachments:
        if attachment.url in allowed_urls:
            safe_attachments.append(attachment)

    result.attachments = safe_attachments
    return result


def _parse_llm_json(raw_content: str) -> dict[str, Any]:
    return json.loads(raw_content)


def _call_llm(input_data: dict[str, Any]) -> str:
    settings = get_settings()
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not configured.")

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(input_data, ensure_ascii=False),
            },
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        settings.llm_api_url,
        headers=headers,
        json=payload,
        timeout=settings.llm_timeout,
    )
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


def standardize_page_content(input_data: dict[str, Any]) -> LLMResult:
    file_links = input_data.get("file_links") or []
    allowed_urls = _allowed_attachment_urls(file_links)

    try:
        raw_content = _call_llm(input_data)
        parsed = _parse_llm_json(raw_content)
        result = LLMResult.model_validate(parsed)
        return _sanitize_attachments(result, allowed_urls)
    except (json.JSONDecodeError, ValidationError) as exc:
        return _failed_result(f"LLM_PARSE_ERROR: {exc}")
    except Exception as exc:
        return _failed_result(str(exc))
