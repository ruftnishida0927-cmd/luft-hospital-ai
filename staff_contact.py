# -*- coding: utf-8 -*-

def get_staff_contact_debug(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    contact = {
        "看護部長": "不明",
        "事務長": "不明",
        "人事担当": "不明",
        "代表電話": "不明",
        "採用窓口": "不明",
        "URL": "",
        "スコア": 0
    }

    debug = {
        "candidate_url_count": 0,
        "page_details": []
    }

    return contact, debug


def get_staff_contact(hospital_name: str, area: str = "", hospital_info: dict | None = None):
    contact, _ = get_staff_contact_debug(hospital_name, area, hospital_info)
    return contact
