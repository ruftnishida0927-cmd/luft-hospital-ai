# -*- coding: utf-8 -*-
import streamlit as st
import time

st.set_page_config(page_title="ルフト病院分析AI", layout="centered")

st.title("ルフト病院分析AI")

hospital = st.text_input("病院名を入力")

if st.button("分析開始"):

    if hospital == "":
        st.warning("病院名を入力してください")
        st.stop()

    st.write("分析中...")
    time.sleep(1)

    st.subheader("取得施設基準")

    acquired = [
        "急性期一般入院料4",
        "看護補助体制加算",
        "医師事務作業補助体制加算"
    ]

    for a in acquired:
        st.write("・", a)

    st.subheader("未取得（取得可能）")

    missing = [
        ("急性期看護補助体制加算25:1", 420),
        ("夜間看護補助加算", 160),
        ("医師事務作業補助体制加算50:1", 300)
    ]

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
