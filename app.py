# -*- coding: utf-8 -*-
import streamlit as st
import time
from hospital_basic import get_hospital_basic_info
from facility_standard import get_facility_standard

st.set_page_config(page_title="ルフト病院分析AI", layout="centered")

st.title("ルフト病院分析AI")

hospital = st.text_input("病院名を入力")

if st.button("分析開始"):

    if hospital == "":
        st.warning("病院名を入力してください")
        st.stop()

    st.write("分析中...")
    time.sleep(1)

info = get_hospital_basic_info(hospital)

st.subheader("病院基本情報")

st.write("病院名:", info["病院名"])
st.write("病床数:", info["病床数"])
st.write("病院種別:", info["病院種別"])
st.write("地域:", info["地域"])
st.write("急性期:", info["急性期"])
st.write("回復期:", info["回復期"])
st.write("療養:", info["療養"])
st.write("診療科:", " / ".join(info["診療科"]))
    
    st.subheader("取得施設基準")

    acquired, missing = get_facility_standard(hospital)

    for a in acquired:
        st.write("・", a)

    st.subheader("未取得（取得可能）")

    total = 0

    for name, point in missing:
        st.write(f"・{name}　(+{point}点/日)")
        total += point

    st.subheader("改善インパクト")

    st.write(f"日次 +{total}点")
    st.write(f"月間 +{total*30}点")
    st.write(f"収益目安 +{total*30}円")

    st.subheader("必要人員")

    st.write("・看護補助 +2名")
    st.write("・医師事務 +1名")

    st.subheader("優先順位")

    st.write("① 医師事務作業補助体制加算")
    st.write("② 夜間看護補助加算")
    st.write("③ 急性期看護補助25:1")

    st.success("分析完了")
