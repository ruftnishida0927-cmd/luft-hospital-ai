from __future__ import annotations

import io
from datetime import datetime
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from .config import MAX_TEXT_CHARS, TIMEOUT, USER_AGENT
from .utils import looks_like_pdf, normalize_space


class Fetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch(self, url: str) -> Tuple[str, str, str, int, str]:
        resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
        content_type = resp.headers.get("Content-Type", "")
        final_url = resp.url
        status = resp.status_code
        body = ""
        title = ""
        if looks_like_pdf(final_url, content_type):
            body = self._read_pdf(resp.content)
            title = final_url.rsplit("/", 1)[-1]
        else:
            resp.encoding = resp.encoding or resp.apparent_encoding
            html = resp.text
            soup = BeautifulSoup(html, "lxml")
            title = normalize_space(soup.title.get_text(" ")) if soup.title else ""
            for tag in soup(["script", "style", "noscript"]):
                tag.extract()
            body = normalize_space(soup.get_text(" "))[:MAX_TEXT_CHARS]
        return final_url, content_type, title, status, body

    def fetch_html(self, url: str) -> Tuple[str, str, str, int, str, str]:
        resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
        resp.encoding = resp.encoding or resp.apparent_encoding
        html = resp.text
        soup = BeautifulSoup(html, "lxml")
        title = normalize_space(soup.title.get_text(" ")) if soup.title else ""
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        body = normalize_space(soup.get_text(" "))[:MAX_TEXT_CHARS]
        return resp.url, resp.headers.get("Content-Type", ""), title, resp.status_code, body, html

    @staticmethod
    def _read_pdf(content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            return normalize_space(text)[:MAX_TEXT_CHARS]
        except Exception:
            return ""

    @staticmethod
    def timestamp() -> str:
        return datetime.utcnow().isoformat()
