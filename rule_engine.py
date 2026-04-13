from __future__ import annotations


def build_summary_markdown(hospital_name: str, profile: list, contacts: list, facilities: list, recruitments: list, phases: list):
    phase = phases[0] if phases else {}
    contact = contacts[0] if contacts else {}
    prof = profile[0] if profile else {}
    lines = [f"## {hospital_name} の営業分析サマリー", ""]
    lines.append(f"- 想定フェーズ: {phase.get('predicted_phase', '要確認')}")
    lines.append(f"- 想定課題: {phase.get('expected_issue', '要確認')}")
    lines.append(f"- 推奨提案職種: {phase.get('recommended_roles', '要確認')}")
    lines.append(f"- 営業優先度: {phase.get('priority_score', '要確認')}")
    lines.append(f"- 採用窓口候補: {contact.get('title', '要確認')} / {contact.get('person_name', '人名未取得')}")
    lines.append(f"- 代表URL: {prof.get('website_url', '未取得')}")
    lines.append("")
    lines.append("### 初動アクション")
    lines.append("- 公式サイトと採用ページの確認")
    lines.append("- 代表窓口へ採用担当部署の確認")
    lines.append("- 現在募集している職種と勤務形態の確認")
    lines.append("")
    lines.append("### 注意")
    lines.append("- 公開情報ベースの推定を含むため、最終確認は病院窓口や公的資料で行ってください。")
    return "\n".join(lines)
