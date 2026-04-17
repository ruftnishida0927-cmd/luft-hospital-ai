from __future__ import annotations

from .config import CATEGORY_HINTS, GROUP_DOMAIN_KEYWORDS, PUBLIC_DOMAIN_KEYWORDS, RECRUIT_DOMAIN_KEYWORDS
from .utils import domain


def classify_url(url: str, anchor_text: str = "", title: str = "") -> str:
    text = f"{url} {anchor_text} {title}".lower()
    for category, hints in CATEGORY_HINTS.items():
        if any(h.lower() in text for h in hints):
            return category
    return "unknown"


def infer_source_type(url: str, category: str) -> str:
    d = domain(url)
    if any(k in d for k in PUBLIC_DOMAIN_KEYWORDS) or category == "public":
        return "public"
    if any(k in d for k in RECRUIT_DOMAIN_KEYWORDS) or category == "recruit":
        return "recruit"
    if any(k in d for k in GROUP_DOMAIN_KEYWORDS) or category == "group":
        return "group"
    return "official"
