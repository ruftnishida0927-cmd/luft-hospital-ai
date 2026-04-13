# -*- coding: utf-8 -*-
import streamlit as st
import time
from hospital_basic import get_hospital_basic_info
from facility_standard import get_facility_standard
from nursing_config import get_nursing_config
from staff_contact import get_staff_contact
from excel_export import export_excel
from dispatch_search import search_dispatch_jobs

st.set_page_config(page_title="ルフト病院分析AI", layout="centered")

st.title("ルフト病院分析AI")

hospital = st.text_input("病院名を入力")

if st.button("分析開始"):

    if hospital == "":
        st.warning("病院名を入力してください")
        st.stop()

    st.write("分析中...")
    time.sleep(1)

    # 病院基本情報（候補複数取得）
    candidates = get_hospital_basic_info(hospital)

    best_info = None
    best_dispatch = []
    best_score = -1

    for cand in candidates:

        dispatch_candidates = search_dispatch_jobs(cand)

        if not dispatch_candidates:
            continue

        top = dispatch_candidates[0]

        score = int(str(top["一致率"]).replace("%",""))

        if score > best_score:
            best_score = score
            best_info = cand
            best_dispatch = dispatch_candidates

    if best_info is None:
        best_info = candidates[0]
        best_dispatch = []

    info = best_info
    dispatch_candidates = best_dispatch

# 候補病院表示
st.subheader("候補病院")

for cand in candidates:
    st.write("-------------")

    if cand == info:
        st.write("★採用候補")

    st.write("病院名:", cand["病院名"])
    st.write("地域:", cand["地域"])
    st.write("最寄駅:", cand["最寄駅"])
    st.write("病床数:", cand["病床数"])

    # 病院基本情報表示
    st.subheader("病院基本情報")

    st.write("病院名:", info["病院名"])
    st.write("病床数:", info["病床数"])
    st.write("病院種別:", info["病院種別"])
    st.write("地域:", info["地域"])
    st.write("急性期:", info["急性期"])
    st.write("回復期:", info["回復期"])
    st.write("療養:", info["療養"])
    st.write("診療科:", " / ".join(info["診療科"]))

    # 看護配置
    nursing = get_nursing_config(hospital)

    st.subheader("看護配置")

    st.write("入院基本料:", nursing["入院基本料"])
    st.write("看護配置:", nursing["看護配置"])
    st.write("看護補助:", nursing["看護補助"])
    st.write("夜間補助:", nursing["夜間補助"])
    st.write("看護必要度:", nursing["看護必要度"])

    # 採用窓口
    contact = get_staff_contact(hospital)

    st.subheader("採用窓口")

    st.write("看護部長:", contact["看護部長"])
    st.write("事務長:", contact["事務長"])
    st.write("人事担当:", contact["人事担当"])
    st.write("代表電話:", contact["代表電話"])
    st.write("採用窓口:", contact["採用窓口"])

    # 施設基準
    st.subheader("取得施設基準")

    acquired, missing = get_facility_standard(hospital)

    for a in acquired:
        st.write("・", a)

    # 派遣求人調査
    st.subheader("派遣求人調査")

    for c in dispatch_candidates:
        st.write("-------------")
        st.write("一致率:", c["一致率"], "%")
        st.write("判定:", c["判定"])
        st.write("最寄駅:", c["最寄駅"])
        st.write("徒歩:", c["徒歩"])
        st.write("地域:", c["地域"])
        st.write("職種:", c["職種"])
        st.write("根拠:", c["根拠"])
        st.write("URL:", c["URL"])

    st.success("分析完了")

    file = export_excel(
        hospital,
        info,
        nursing,
        contact,
        acquired,
        missing
    )

    st.download_button(
        "Excelダウンロード",
        open(file, "rb"),
        file_name=file
    )
