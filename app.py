# -*- coding: utf-8 -*-
import streamlit as st
import time
import traceback

from hospital_basic import get_hospital_basic_info_debug
from facility_standard import get_facility_standard, get_facility_standard_debug
from nursing_config import get_nursing_config, get_nursing_config_debug
from staff_contact import get_staff_contact, get_staff_contact_debug
from excel_export import export_excel

st.set_page_config(page_title="ルフト病院分析AI", layout="centered")

st.title("ルフト病院分析AI")

hospital = st.text_input("病院名を入力")
area = st.text_input("都道府県または市区町村（任意・精度向上用）")

# ★ここ変更（デフォルトOFF）
debug_mode = st.checkbox("デバッグ情報を表示する", value=False)

if st.button("分析開始"):

    if hospital == "":
        st.warning("病院名を入力してください")
        st.stop()

    st.write("分析中...")
    time.sleep(0.5)  # ★軽量化（短縮）

    info = None
    candidates = []
    hospital_debug = None

    acquired = []
    missing = []
    facility_debug = None

    nursing = None
    nursing_debug = None

    contact = None
    contact_debug = None

    # ==============================
    # 1. 病院検索
    # ==============================
    st.subheader("① 病院検索")

    try:
        candidates, hospital_debug = get_hospital_basic_info_debug(hospital, area)
        info = candidates[0]

        st.success("病院検索 OK")
        st.write("候補数:", len(candidates))
        st.write("採用候補:", info.get("病院名", ""))
        st.write("住所:", info.get("住所", ""))
        st.write("地域:", info.get("地域", ""))
        st.write("最寄駅:", info.get("最寄駅", ""))
        st.write("病床数:", info.get("病床数", ""))

    except Exception:
        st.error("病院検索でエラー")
        st.code(traceback.format_exc())
        st.stop()

    # ★デバッグ表示（OFFなら出ない）
    if debug_mode and hospital_debug:
        st.subheader("病院検索デバッグ")
        st.write("入力病院名:", hospital_debug.get("input_name", ""))
        st.write("入力エリア:", hospital_debug.get("input_area", ""))
        st.write("検索結果件数:", hospital_debug.get("search_results_count", 0))
        st.write("候補URL件数:", hospital_debug.get("candidate_source_count", 0))
        st.write("本文取得成功件数:", hospital_debug.get("page_fetch_success_count", 0))
        st.write("有効候補件数:", hospital_debug.get("valid_candidate_count", 0))

    st.subheader("候補病院")
    for i, cand in enumerate(candidates):
        st.write("-------------")
        if i == 0:
            st.write("★採用候補")
        st.write("スコア:", cand.get("スコア", 0))
        st.write("取得元:", cand.get("取得元", ""))
        st.write("病院名:", cand.get("病院名", ""))
        st.write("住所:", cand.get("住所", ""))
        st.write("地域:", cand.get("地域", ""))
        st.write("最寄駅:", cand.get("最寄駅", ""))
        st.write("病床数:", cand.get("病床数", ""))
        st.write("URL:", cand.get("URL", ""))

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
    # 2. 施設基準
    # ==============================
    st.subheader("② 施設基準検索")

    try:
        if debug_mode:
            acquired, missing, facility_debug = get_facility_standard_debug(
                hospital,
                area,
                info
            )
        else:
            acquired, missing = get_facility_standard(
                hospital,
                area,
                info
            )

        st.success("施設基準検索 OK")
        st.write("取得件数:", len(acquired))
        for a in acquired:
            st.write("・", a)

    except Exception:
        st.error("施設基準検索でエラー")
        st.code(traceback.format_exc())
        st.stop()

    if debug_mode and facility_debug:
        st.subheader("施設基準検索デバッグ")
        st.write("候補URL件数:", facility_debug.get("candidate_url_count", 0))
        st.write("base_standard:", facility_debug.get("base_standard", ""))
        st.write("base_family:", facility_debug.get("base_family", ""))

        for d in facility_debug.get("page_details", []):
            st.write("-------------")
            st.write("title:", d.get("title", ""))
            st.write("url:", d.get("url", ""))
            st.write("fetched:", d.get("fetched", False))
            st.write("text_len:", d.get("text_len", 0))
            st.write("base_standard:", d.get("base_standard", ""))
            st.write("base_hits:", " / ".join(d.get("base_hits", [])))
            st.write("additional_standards:", " / ".join(d.get("additional_standards", [])))

    # ==============================
    # 精度チェック
    # ==============================
    if info.get("スコア", 0) < 70:
        st.warning("病院特定の精度が低いため停止")
        st.stop()

    if info.get("地域", "不明") == "不明":
        st.warning("地域が特定できていないため停止")
        st.stop()

    if info.get("住所", "") == "":
        st.warning("住所が特定できていないため停止")
        st.stop()

    # ==============================
    # 3. 看護配置
    # ==============================
    st.subheader("③ 看護配置")

    try:
        if debug_mode:
            nursing, nursing_debug = get_nursing_config_debug(hospital, area, info)
        else:
            nursing = get_nursing_config(hospital, area, info)

        st.success("看護配置推定 OK")
        st.write("入院基本料:", nursing.get("入院基本料", ""))
        st.write("看護配置:", nursing.get("看護配置", ""))
        st.write("看護補助:", nursing.get("看護補助", ""))
        st.write("夜間補助:", nursing.get("夜間補助", ""))
        st.write("看護必要度:", nursing.get("看護必要度", ""))

    except Exception:
        st.error("看護配置でエラー")
        st.code(traceback.format_exc())
        st.stop()

    # ==============================
    # 4. 採用窓口
    # ==============================
    st.subheader("④ 採用窓口")

    try:
        if debug_mode:
            contact, contact_debug = get_staff_contact_debug(hospital, area, info)
        else:
            contact = get_staff_contact(hospital, area, info)

        st.success("採用窓口取得 OK")
        st.write("看護部長:", contact.get("看護部長", ""))
        st.write("事務長:", contact.get("事務長", ""))
        st.write("人事担当:", contact.get("人事担当", ""))
        st.write("代表電話:", contact.get("代表電話", ""))
        st.write("採用窓口:", contact.get("採用窓口", ""))

    except Exception:
        st.error("採用窓口でエラー")
        st.code(traceback.format_exc())
        st.stop()

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
