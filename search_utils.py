from __future__ import annotations

from typing import List
from src.models import PhaseSignal
from src.rule_engine import load_latest_policy_rules


def estimate_phase(hospital_name: str, facility_standards: List[dict], recruitment_signals: List[dict], reimbursement_signals: List[dict]):
    facility_text = " ".join((x.get("standard_name") or "") + " " + (x.get("category") or "") for x in facility_standards)
    recruit_text = " ".join((x.get("job_type") or "") + " " + (x.get("comment") or "") for x in recruitment_signals)
    rules = load_latest_policy_rules()
    policy_titles = " / ".join([r.get("title", "") for r in rules[:3] if r.get("title")])

    predicted_phase = "総合分析フェーズ"
    expected_issue = "人員不足・周辺業務の再配分・採用難への対応"
    sales_angle = "看護補助、医療事務、医師事務作業補助者を中心に提案"
    recommended_roles = "看護補助者 / 医療事務 / 医師事務作業補助者"
    priority = 55

    if "急性期" in facility_text or "ICU" in facility_text or "HCU" in facility_text:
        predicted_phase = "急性期強化フェーズ"
        expected_issue = "病棟支援人材不足、医師・看護師の周辺業務負荷"
        sales_angle = "看護補助、病棟クラーク、医師事務の提案が有効"
        recommended_roles = "看護補助者 / 病棟クラーク / 医師事務作業補助者"
        priority = 80
    elif "回復期" in facility_text or "地域包括" in facility_text:
        predicted_phase = "回復期・地域包括最適化フェーズ"
        expected_issue = "入退院調整、病棟運営支援、事務負荷"
        sales_angle = "病棟支援系と事務系の提案が有効"
        recommended_roles = "看護補助者 / 医療事務 / クラーク"
        priority = 72
    elif "慢性期" in facility_text or "療養" in facility_text:
        predicted_phase = "慢性期効率化フェーズ"
        expected_issue = "介助補助・環境整備・周辺業務負担"
        sales_angle = "看護補助、入浴介助、シーツ交換などの提案が有効"
        recommended_roles = "看護補助者 / 入浴介助 / シーツ交換"
        priority = 68
    elif "在宅" in facility_text or "訪問診療" in facility_text:
        predicted_phase = "在宅拡大フェーズ"
        expected_issue = "訪問調整、バックオフィス、電話対応負担"
        sales_angle = "医療事務、訪問調整、コール対応の提案が有効"
        recommended_roles = "医療事務 / 事務補助 / コールセンター"
        priority = 70

    if "医療事務" in recruit_text or "看護補助" in recruit_text or "看護助手" in recruit_text:
        priority += 8

    signal_detail = policy_titles or "最新制度差分を反映しつつ、公開情報から営業仮説を生成"

    return [
        PhaseSignal(
            hospital_name=hospital_name,
            signal_type="運営フェーズ仮説",
            signal_detail=signal_detail,
            predicted_phase=predicted_phase,
            expected_issue=expected_issue,
            sales_angle=sales_angle,
            recommended_roles=recommended_roles,
            priority_score=min(priority, 100),
        ).model_dump()
    ]
