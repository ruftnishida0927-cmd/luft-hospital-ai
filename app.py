# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup

st.title("ルフト病院分析AI")

hospital = st.text_input("病院名を入力")

def search_facility(hospital_name):
    try:
        url = "https://www.mhlw.go.jp/"
        return "施設基準取得準備中"
    except:
        return "取得失敗"

if st.button("分析開始"):
    st.write("分析中...")

    facility = search_facility(hospital)

    st.subheader("施設基準")
    st.write(facility)

    st.success("分析完了")
