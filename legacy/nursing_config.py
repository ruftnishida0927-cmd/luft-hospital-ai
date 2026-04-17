# -*- coding: utf-8 -*-
from facility_standard import get_facility_standard_debug


def _detect_base_info(acquired):
    """
    施設基準一覧から基礎となる入院料系統を判定
    """
    base_standard = None
    base_family = "不明"

    for item in acquired:
        if "急性期一般入院料" in item:
            base_standard = item
            base_family = "急性期"
            break

        if "地域一般入院料" in item:
            base_standard = item
            base_family = "地域一般"
            break

        if "障害者施設等入院基本料" in item:
            base_standard = item
            base_family = "障害者"
            break

        if "療養病棟入院基本料" in item:
            base_standard = item
            base_family = "療養"
            break

        if "地域包括ケア病棟入院料" in item:
            base_standard = item
            base_family = "包括ケア"
            break

        if "回復期リハビリテーション病棟入院料" in item:
            base_standard = item
            base_family = "回復期"
            break

    return base_standard, base_family


def _map_nursing_ratio(base_standard, base_family):
    """
    基本料から看護配置をマッピング
    """
    if not base_standard:
        return "不明"

    acute_map = {
        "急性期一般入院料1": "7:1",
        "急性期一般入院料2": "7:1",
        "急性期一般入院料3": "10:1",
        "急性期一般入院料4": "10:1",
        "急性期一般入院料5": "10:1",
        "急性期一般入院料6": "10:1",
    }

    regional_map = {
        "地域一般入院料1": "13:1",
        "地域一般入院料2": "13:1",
        "地域一般入院料3": "15:1",
    }

    if base_family == "急性期":
        return acute_map.get(base_standard, "不明")

    if base_family == "地域一般":
        return regional_map.get(base_standard, "不明")

    if base_family == "障害者":
        # 公開情報上は13:1が多いが、病院により差があるため断定は控えめ
        return "13:1"

    if base_family == "療養":
        return "20:1相当"

    if base_family == "包括ケア":
        return "13:1相当"

    if base_family == "回復期":
        return "13:1相当"

    return "不明"


def _detect_nursing_assist(acquired, base_family):
    """
    看護補助関連の有無
    """
    if "急性期看護補助体制加算" in acquired:
        return "あり（急性期看護補助体制加算）"

    if "看護補助体制加算" in acquired:
        return "あり（看護補助体制加算）"

    if "看護補助加算2" in acquired:
        return "あり（看護補助加算2）"

    if "看護補助加算1" in acquired:
        return "あり（看護補助加算1）"

    if "看護補助加算" in acquired:
        return "あり（看護補助加算）"

    if base_family in ["障害者", "療養"]:
        return "不明"

    return "なし"


def _detect_night_assist(acquired, base_family):
    """
    夜間補助関連
    """
    if "夜間看護補助加算" in acquired:
        return "あり（夜間看護補助加算）"

    if base_family in ["障害者", "療養", "急性期", "地域一般"]:
        return "不明"

    return "なし"


def _detect_need_level(base_family):
    """
    看護必要度っぽい表示
    """
    if base_family == "急性期":
        return "あり（急性期評価系の可能性）"

    if base_family in ["障害者", "療養", "回復期", "包括ケア"]:
        return "病棟区分に応じた評価"

    if base_family == "地域一般":
        return "不明"

    return "不明"


def get_nursing_config_debug(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    acquired, missing, facility_debug = get_facility_standard_debug(
        hospital_name,
        area,
        hospital_info
    )

    base_standard, base_family = _detect_base_info(acquired)

    nursing = {
        "入院基本料": base_standard or "不明",
        "看護配置": _map_nursing_ratio(base_standard, base_family),
        "看護補助": _detect_nursing_assist(acquired, base_family),
        "夜間補助": _detect_night_assist(acquired, base_family),
        "看護必要度": _detect_need_level(base_family),
    }

    debug = {
        "base_standard": base_standard or "不明",
        "base_family": base_family,
        "facility_acquired": acquired,
        "facility_missing": missing,
        "facility_debug": facility_debug
    }

    return nursing, debug


def get_nursing_config(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    nursing, _ = get_nursing_config_debug(
        hospital_name,
        area,
        hospital_info
    )
    return nursing
