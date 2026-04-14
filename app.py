# -*- coding: utf-8 -*-
import streamlit as st
import time

from hospital_basic import get_hospital_basic_info
from facility_standard import get_facility_standard
from nursing_config import get_nursing_config
from staff_contact import get_staff_contact
from excel_export import export_excel

st.set_page_config(page_title="ルフト病院分析AI", layout="centered")

st.title("ルフト病院分析AI")

hospital = st.text_input("病院名を入力")
area = st.text_input("都道府県または市区町村（任意・精度向上用）")

if st.button("分析開始"):

    if hospital == "":
        st.warning("病院名を入力してください")
        st.stop()

    st.write("分析中...")
    time.sleep(1)

    # ==============================
    # 病院候補取得
    # ==============================
    candidates = get_hospital_basic_info(hospital, area)
    info = candidates[0]

    # ==============================
    # 候補病院表示
    # ==============================
    st.subheader("候補病院")
    st.write("候補数:", len(candidates))

    for i, cand in enumerate(candidates):
        st.write("-------------")

        if i == 0:
            st.write("★採用候補")

        st.write("スコア:", cand.get("スコア", 0))
        st.write("取得元:", cand.get("取得元", ""))

        source_list = cand.get("取得元一覧", [])
        if source_list:
            st.write("取得元一覧:", " / ".join(source_list))

        st.write("病院名:", cand.get("病院名", ""))
        st.write("住所:", cand.get("住所", ""))
        st.write("地域:", cand.get("地域", ""))
        st.write("最寄駅:", cand.get("最寄駅", ""))
        st.write("病床数:", cand.get("病床数", ""))
        st.write("診療科:", " / ".join(cand.get("診療科", [])))
        st.write("URL:", cand.get("URL", ""))

    # ==============================
    # 病院基本情報
    # ==============================
    st.subheader("病院基本情報")

    st.write("病院名:", info.get("病院名", ""))
    st.write("病院種別:", info.get("病院種別", ""))
    st.write("住所:", info.get("住所", ""))
    st.write("地域:", info.get("地域", ""))
    st.write("最寄駅:", info.get("最寄駅", ""))
    st.write("病床数:", info.get("病床数", ""))
    st.write("急性期:", info.get("急性期", False))
    st.write("回復期:", info.get("回復期", False))
    st.write("療養:", info.get("療養", False))
    st.write("診療科:", " / ".join(info.get("診療科", [])))
    st.write("取得元:", info.get("取得元", ""))
    st.write("URL:", info.get("URL", ""))

    # ==============================
    # 病院特定チェック
    # ==============================
    if info.get("スコア", 0) < 70:
        st.error("病院特定の精度が低いため、後続処理を停止しました。候補病院を確認してください。")
        st.stop()

    if info.get("地域", "不明") == "不明":
        st.error("地域が特定できていないため、後続処理を停止しました。")
        st.stop()

    if info.get("住所", "") == "":
        st.error("住所が特定できていないため、後続処理を停止しました。")
        st.stop()

    # ==============================
    # 看護配置
    # ==============================
    nursing = get_nursing_config(hospital)

    st.subheader("看護配置")
    st.write("入院基本料:", nursing["入院基本料"])
    st.write("看護配置:", nursing["看護配置"])
    st.write("看護補助:", nursing["看護補助"])
    st.write("夜間補助:", nursing["夜間補助"])
    st.write("看護必要度:", nursing["看護必要度"])

    # ==============================
    # 採用窓口
    # ==============================
    contact = get_staff_contact(hospital)

    st.subheader("採用窓口")
    st.write("看護部長:", contact["看護部長"])
    st.write("事務長:", contact["事務長"])
    st.write("人事担当:", contact["人事担当"])
    st.write("代表電話:", contact["代表電話"])
    st.write("採用窓口:", contact["採用窓口"])

    # ==============================
    # 施設基準
    # ==============================
    st.subheader("取得施設基準")
    acquired, missing = get_facility_standard(hospital)

    for a in acquired:
        st.write("・", a)

    st.success("分析完了")

    # ==============================
    # Excel出力
    # ==============================
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
