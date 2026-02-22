import streamlit as st
from pages.modules import util_sidebar

def main():

    util_sidebar()

    # Основной контент главной страницы
    st.title("Домашняя страница")
    st.write("Добро пожаловать в наше приложение!")

if __name__ == "__main__":
    main()
