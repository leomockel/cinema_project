import streamlit as st


def load_css(file_path: str):
    """Charge un fichier CSS externe dans Streamlit"""
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")


def load_multiple_css(file_paths: list):
    """Charge plusieurs fichiers CSS en une fois"""
    for file_path in file_paths:
        load_css(file_path)