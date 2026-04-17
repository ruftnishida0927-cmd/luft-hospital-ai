from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Dict, List

from .models import Evidence, ResolvedField
from .utils import guess_consistency, normalize_space, unique_keep_order

PRIORITY_FIELDS = [
    "住所", "地域", "最寄駅", "病床数", "診療科", "病院種別", "病院機能", "法人名", "代表電話", "メール"
]


def resolve_fields(evidences: Dict[str, List[Evidence]]) -> Dict[str, ResolvedField]:
    resolved = {}
    for field in PRIORITY_FIELDS:
        evs = evidences.get(field, [])
        resolved[field] = _resolve_single(field, evs)
    return resolved


def resolve_recruit(evidences: Dict[str, List[Evidence]]) -> Dict[str, ResolvedField]:
    fields = ["採用担当部署", "採用電話", "採用メール"]
    return {f: _resolve_single(f, evidences.get(f, [])) for f in fields}


def resolve_group(evidences: Dict[str, List[Evidence]]) -> List[ResolvedField]:
    out = []
    for key in ["関連法人候補", "関連施設候補"]:
        by_value = _group_by_value(evidences.get(key, []))
        for value, evs in by_value.items():
            out.append(ResolvedField(key, value, evs[:5], guess_consistency([e.value for e in evs]), "複数ページに同一候補が見られる場合を優先"))
    out.sort(key=lambda x: _agg_score(x.evidences), reverse=True)
    return out[:12]


def resolve_facility_lists(evidences: Dict[str, List[Evidence]]):
    basic = _resolve_facility_bucket(evidences.get("施設基準_基本料", []), "施設基準_基本料")
    addons = _resolve_facility_bucket(evidences.get("施設基準_加算", []), "施設基準_加算")
    return basic, addons


def _resolve_single(field: str, evs: List[Evidence]) -> ResolvedField:
    if not evs:
        return ResolvedField(field, "不明", [], "不明", "十分な根拠が見つからないため不明とした")

    normalized_groups = defaultdict(list)
    for ev in evs:
        normalized_groups[_normalize_field_value(field, ev.value)].append(ev)

    best_value, best_evs = sorted(normalized_groups.items(), key=lambda kv: (_agg_score(kv[1]), len(kv[1])), reverse=True)[0]
    consistency = guess_consistency([ev.value for ev in evs])
    comment = _build_comment(field, best_evs, consistency)
    return ResolvedField(field, best_value, sorted(best_evs, key=lambda e: e.confidence, reverse=True)[:5], consistency, comment)


def _resolve_facility_bucket(evs: List[Evidence], field_name: str) -> List[ResolvedField]:
    cleaned = []
    for ev in evs:
        values = _split_facility_value(ev.value)
        for v in values:
            cleaned.append(Evidence(field_name, v, ev.source_url, ev.source_label, ev.category, ev.source_type, ev.confidence, ev.extracted_by, ev.comment))

    grouped = _group_by_value(cleaned)
    out = []
    for value, items in grouped.items():
        if len(value) < 4:
            continue
        consistency = guess_consistency([i.value for i in items])
        out.append(ResolvedField(field_name, value, sorted(items, key=lambda e: e.confidence, reverse=True)[:5], consistency, "病院HPと公的ソースを優先して集約"))
    out.sort(key=lambda x: (_agg_score(x.evidences), len(x.evidences)), reverse=True)
    return out[:50]


def _group_by_value(evs: List[Evidence]):
    grouped = defaultdict(list)
    for ev in evs:
        grouped[_normalize_generic(ev.value)].append(ev)
    return grouped


def _normalize_field_value(field: str, value: str) -> str:
    value = normalize_space(value)
    if field == "住所":
        value = re.sub(r"〒\d{3}-\d{4}", "", value)
    if field == "診療科":
        parts = unique_keep_order(re.split(r"[、,／/\s]+", value))
        value = "、".join(sorted([p for p in parts if p]))
    return value or "不明"


def _normalize_generic(value: str) -> str:
    value = normalize_space(value)
    value = re.sub(r"\s+", " ", value)
    return value


def _split_facility_value(value: str) -> List[str]:
    value = normalize_space(value)
    parts = re.split(r"[、,／/]|\s{2,}", value)
    out = []
    for p in parts:
        p = normalize_space(p)
        if not p:
            continue
        if any(kw in p for kw in ["入院料", "基本料", "加算", "補助体制", "対策", "体制"]):
            out.append(p)
    return out or [value]


def _agg_score(evs: List[Evidence]) -> float:
    return round(sum(e.confidence for e in evs), 4)


def _build_comment(field: str, evs: List[Evidence], consistency: str) -> str:
    source_types = unique_keep_order([e.source_type for e in evs])
    if consistency in {"一致", "多数一致"} and "public" in source_types and "official" in source_types:
        return "公的ソースと公式ソースの双方で整合しやすい値を採用"
    if consistency in {"一致", "多数一致"} and "official" in source_types:
        return "公式サイト内の複数ページで一致した値を採用"
    if consistency == "一部不一致":
        return "候補に差異があるため、ソース種別と一致数の高い値を暫定採用"
    return "根拠が限定的なため暫定採用。矛盾が残る場合は追加確認が必要"
