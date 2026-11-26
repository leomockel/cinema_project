import streamlit as st
from src.config.settings import PAGE_CONFIG, IMAGES_DIR, SESSION_DICT
from src.services.db_connect import load_movies, load_users
from src.pages.home_page import home_page
from src.pages.scrap_page import scrap_page


############################################
# Page configuration
############################################

st.set_page_config(**PAGE_CONFIG)

st.markdown(
    """
    <style>
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0f0f0f !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

############################################
# Session defaults
############################################

if 'movies' not in st.session_state:
    st.session_state.movies = load_movies()
if 'users' not in st.session_state:
    st.session_state.users = load_users()

for key, value in SESSION_DICT.items():
    st.session_state.setdefault(key, value)


############################################
#  Navigation
############################################

pages = {
    "Accueil": st.Page(home_page, title="Accueil", icon="🏠"),
    "Scrap": st.Page(scrap_page, title="Scrap", icon="🔍")
}

pg = st.navigation(list(pages.values()), position="top")
pg.run()