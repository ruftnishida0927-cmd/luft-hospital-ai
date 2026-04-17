from __future__ import annotations

import json
import re
from collections import Counter
from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlparse


def normalize_space(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def strip_fragment(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}" + (f"?{p.query}" if p.query else "")


def same_domain(url1: str, url2: str) -> bool:
    try:
        return urlparse(url1).netloc == urlparse(url2).netloc
    except Exception:
        return False


def to_abs(base: str, href: str) -> str:
    return strip_fragment(urljoin(base, href))


def domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def looks_like_pdf(url: str, content_type: str = "") -> bool:
    url = url.lower()
    return url.endswith(".pdf") or "pdf" in content_type.lower()


def is_japanese_address(text: str) -> bool:
    return bool(re.search(r"(都|道|府|県).+(市|区|町|村)", text or ""))


def extract_prefecture(text: str) -> str:
    m = re.search(r"(北海道|東京都|京都府|大阪府|.{2,3}県)", text or "")
    return m.group(1) if m else "不明"


def unique_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def guess_consistency(values: List[str]) -> str:
    vals = [normalize_space(v) for v in values if normalize_space(v)]
    if not vals:
        return "不明"
    counts = Counter(vals)
    if len(counts) == 1 and len(vals) >= 2:
        return "一致"
    top, top_n = counts.most_common(1)[0]
    if top_n >= 2:
        return "多数一致"
    if len(counts) >= 2:
        return "一部不一致"
    return "不明"


def dumps_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
