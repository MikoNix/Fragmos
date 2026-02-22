import streamlit as st
from pages.modules import util_sidebar
from pathlib import Path

util_sidebar()

st.markdown("## ТУТ НИЧЕГО НЕТ ПОКА ЧТО ")

# Автопоиск файла quality=95.gif
base_dir = Path(__file__).resolve().parent
gif_path = next(base_dir.rglob("quality=95.gif"), None)

st.image(str(gif_path))