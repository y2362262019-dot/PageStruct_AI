from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urlparse

import requests
from requests import Response


DEFAULT_TIMEOUT = 15
MAX_RETRIES = 1
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "PageStructAI/0.1 Safari/537.36"
)


def _build_result(
    *,
    url: str,
    final_url: str = "",
    fetch_status: str,
    http_status: Optional[int] = None,
    html: str = "",
    error_message: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "url": url,
        "final_url": final_url,
        "fetch_status": fetch_status,
        "http_status": http_status,
        "html": html,
        "error_message": error_message,
    }


def _is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _response_to_result(url: str, response: Response) -> dict[str, Any]:
    if response.status_code >= 400:
        return _build_result(
            url=url,
            final_url=response.url,
            fetch_status="HTTP_ERROR",
            http_status=response.status_code,
            error_message=f"HTTP status {response.status_code}",
        )

    response.encoding = response.encoding or response.apparent_encoding
    return _build_result(
        url=url,
        final_url=response.url,
        fetch_status="SUCCESS",
        http_status=response.status_code,
        html=response.text,
    )


def fetch_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    normalized_url = url.strip()
    if not _is_allowed_url(normalized_url):
        return _build_result(
            url=normalized_url,
            fetch_status="INVALID_URL",
            error_message="Only http and https URLs are supported.",
        )

    headers = {"User-Agent": USER_AGENT}
    last_error: Optional[str] = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(
                normalized_url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )
            return _response_to_result(normalized_url, response)
        except requests.Timeout as exc:
            last_error = str(exc)
            fetch_status = "TIMEOUT"
        except requests.exceptions.SSLError as exc:
            last_error = str(exc)
            fetch_status = "SSL_ERROR"
            break
        except requests.exceptions.ConnectionError as exc:
            last_error = str(exc)
            fetch_status = "NETWORK_ERROR"
        except requests.RequestException as exc:
            last_error = str(exc)
            fetch_status = "UNKNOWN_ERROR"
            break
        except Exception as exc:
            last_error = str(exc)
            fetch_status = "UNKNOWN_ERROR"
            break

        if attempt >= MAX_RETRIES:
            break

    return _build_result(
        url=normalized_url,
        fetch_status=fetch_status,
        error_message=last_error,
    )
