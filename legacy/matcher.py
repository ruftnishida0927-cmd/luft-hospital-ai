def calc_match_score(hospital, job):

    score = 0
    reasons = []

    # 地域一致
    if hospital["地域"] != "不明" and hospital["地域"] in job["text"]:
        score += 30
        reasons.append("地域一致")

    # 最寄駅一致
    if hospital["最寄駅"] != "不明" and hospital["最寄駅"] in job["text"]:
        score += 40
        reasons.append("最寄駅一致")

    # 病院名一致
    if hospital["病院名"] in job["text"]:
        score += 50
        reasons.append("病院名一致")

    # 徒歩一致
    if "徒歩" in job["text"]:
        score += 10
        reasons.append("徒歩情報")

    return score, reasons
