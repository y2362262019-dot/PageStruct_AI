from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup


FILE_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "zip",
    "rar",
    "txt",
    "csv",
}
FILE_KEYWORDS = {
    "下载",
    "附件",
    "点击下载",
    "文件",
    "正文",
    "pdf",
    "word",
    "excel",
    "申报表",
    "名单",
    "通知书",
    "附件1",
    "附件2",
}


def clean_text(text: str) -> str:
    lines = [re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in text.splitlines()]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines)


def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.find(["h1", "h2"])
    return heading.get_text(" ", strip=True) if heading else ""


def extract_text(soup: BeautifulSoup) -> tuple[str, str]:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    raw_text = soup.get_text("\n")
    return raw_text, clean_text(raw_text)


def _file_type_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path)
    suffix = PurePosixPath(path).suffix.lower().lstrip(".")
    return suffix if suffix in FILE_EXTENSIONS else ""


def _file_name_from_url(url: str, link_text: str) -> str:
    parsed = urlparse(url)
    name = PurePosixPath(unquote(parsed.path)).name
    return name or link_text


def _is_file_link(text: str, url: str) -> bool:
    if _file_type_from_url(url):
        return True

    normalized_text = text.strip().lower()
    return any(keyword.lower() in normalized_text for keyword in FILE_KEYWORDS)


def extract_links(soup: BeautifulSoup, base_url: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for tag in soup.find_all("a"):
        href = tag.get("href")
        if not href:
            continue

        absolute_url = urljoin(base_url, href.strip())
        parsed = urlparse(absolute_url)
        if parsed.scheme not in {"http", "https"}:
            continue

        text = tag.get_text(" ", strip=True)
        item = (text, absolute_url)
        if item in seen:
            continue

        seen.add(item)
        links.append({"text": text, "url": absolute_url})

    return links


def extract_file_links(links: list[dict[str, str]]) -> list[dict[str, str]]:
    file_links: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for link in links:
        text = link["text"]
        url = link["url"]
        if url in seen_urls or not _is_file_link(text, url):
            continue

        file_type = _file_type_from_url(url)
        file_links.append(
            {
                "text": text,
                "url": url,
                "file_name": _file_name_from_url(url, text),
                "file_type": file_type,
            }
        )
        seen_urls.add(url)

    return file_links


def extract_page_content(html: str, base_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html or "", "html.parser")
    title = extract_title(soup)
    links = extract_links(soup, base_url)
    raw_text, cleaned_text = extract_text(soup)
    file_links = extract_file_links(links)

    return {
        "title": title,
        "raw_text": raw_text,
        "clean_text": cleaned_text,
        "links": links,
        "file_links": file_links,
    }
