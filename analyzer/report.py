from __future__ import annotations

from typing import Dict, List

from .models import AnalysisResult, Evidence, ResolvedField


def format_resolved_markdown(title: str, rf: ResolvedField) -> str:
    lines = [f"### {title}", f"① 最終判断: {rf.final_value}", f"③ 整合性: {rf.consistency}", f"④ コメント: {rf.comment}", "② 根拠ソース:"]
    if not rf.evidences:
        lines.append("- 根拠不足")
    else:
        for ev in rf.evidences:
            lines.append(f"- {ev.source_type}/{ev.category} | {ev.source_label} | {ev.source_url} | 抽出値: {ev.value}")
    return "\n".join(lines)


def build_summary(result: AnalysisResult) -> str:
    lines = [f"# ルフト病院分析AI レポート", f"- 対象病院: {result.hospital_name or '不明'}", f"- 基準URL: {result.canonical_url}", ""]
    lines.append("## 基本情報")
    for key in ["住所", "地域", "最寄駅", "病床数", "診療科", "病院種別", "病院機能", "法人名", "代表電話", "メール"]:
        lines.append(format_resolved_markdown(key, result.resolved.get(key)))
        lines.append("")

    lines.append("## 施設基準 / 基本料系")
    if not result.facility_basic_fee:
        lines.append("- 不明")
    for item in result.facility_basic_fee:
        lines.append(format_resolved_markdown(item.final_value, item))
        lines.append("")

    lines.append("## 施設基準 / 加算系")
    if not result.facility_addons:
        lines.append("- 不明")
    for item in result.facility_addons:
        lines.append(format_resolved_markdown(item.final_value, item))
        lines.append("")

    lines.append("## 求人窓口")
    for key, rf in result.recruit_fields.items():
        lines.append(format_resolved_markdown(key, rf))
        lines.append("")

    lines.append("## グループ / 関連法人")
    if not result.group_entities:
        lines.append("- 不明")
    for item in result.group_entities:
        lines.append(format_resolved_markdown(item.field_name, item))
        lines.append("")

    if result.notes:
        lines.append("## 補足")
        for n in result.notes:
            lines.append(f"- {n}")
    return "\n".join(lines)
