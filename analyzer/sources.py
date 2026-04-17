from __future__ import annotations

from typing import Dict, List, Tuple
from urllib.parse import urlparse

from .models import Page


def summarize_sources(pages: List[Page]) -> Dict[str, List[str]]:
    out = {"official": [], "public": [], "recruit": [], "group": []}
    for p in pages:
        if p.source_type in out:
            out[p.source_type].append(p.final_url)
    return {k: sorted(set(v)) for k, v in out.items()}


def detect_missing_source_layers(pages: List[Page]) -> List[str]:
    counts = summarize_sources(pages)
    notes = []
    if not counts["public"]:
        notes.append("公的ソース候補の自動発見ができていない。公式サイト外への明示リンクが無い可能性がある。")
    if not counts["recruit"]:
        notes.append("求人ソース候補の自動発見ができていない。採用ページ未掲載または外部求人導線未検出の可能性がある。")
    if not counts["group"]:
        notes.append("グループ/法人ソース候補の自動発見が限定的。法人案内ページが無いか、リンクが浅い可能性がある。")
    return notes
