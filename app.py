# -*- coding: utf-8 -*-
import streamlit as st

st.title("ルフト病院分析AI")

hospital = st.text_input("病院名を入力")

if st.button("分析開始"):
    st.write("分析中...")
    st.write("病院名:", hospital)
    st.success("分析完了（デモ）")
