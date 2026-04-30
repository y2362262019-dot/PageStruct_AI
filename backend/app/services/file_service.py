from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.utils.url_utils import is_http_url


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "storage" / "uploads"
SUPPORTED_FILE_TYPES = {"csv", "xlsx"}


def safe_upload_filename(filename: str) -> str:
    path = Path(filename)
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem).strip("._") or "upload"
    suffix = path.suffix.lower()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    return f"{stem}_{timestamp}{suffix}"


def get_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    return suffix if suffix in SUPPORTED_FILE_TYPES else ""


def save_upload_file(filename: str, content: bytes) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / safe_upload_filename(filename)
    file_path.write_bytes(content)
    return str(file_path)


def read_url_rows(file_path: str, file_type: str, url_column: str) -> tuple[list[str], int]:
    if file_type == "csv":
        dataframe = pd.read_csv(file_path)
    elif file_type == "xlsx":
        dataframe = pd.read_excel(file_path)
    else:
        raise ValueError("仅支持 CSV 和 XLSX 文件。")

    if url_column not in dataframe.columns:
        raise ValueError(f"文件中不存在 URL 列：{url_column}")

    values: list[Any] = dataframe[url_column].dropna().tolist()
    urls = [str(value).strip() for value in values]
    valid_urls = [url for url in urls if is_http_url(url)]
    return valid_urls, len(dataframe)
