import streamlit as st
import pandas as pd
import time
import re
from src.components.UX_helper import show_message
from src.components.UX_helper import apply_page_styles
from src.config.settings import IMAGES_DIR
from src.services.process import update_user_movies, clear_form_callback
from src.services.db_connect import load_actors


def home_page():

    # 1. On applique le fond et les CSS spécifiques à CETTE page dès son chargement
    apply_page_styles(
        bg_image_path=IMAGES_DIR / "movie_wallpaper.png", 
        css_files=["src/styles/themes.css", "src/styles/home_components.css"]
    )
    st.markdown(
        "<div style='text-align: center;'><h1 class='custom-header'>🎬 Recherche et mise à jour des films</h1></div>", 
        unsafe_allow_html=True
    )

    movies = st.session_state.movies
    users = st.session_state.users

    movies[["french_title", "original_title"]] = movies[["french_title", "original_title"]].astype(str)

    # --- Metrics ---
    if not users.empty:
        nb_vus = users["saw"].sum()
        nb_wishlist = users["wishlist"].sum()
    else:
        nb_vus = 0
        nb_wishlist = 0

    _, vu, wishlist, _ = st.columns([1, 1, 1, 1])
    with vu:    
        st.metric("Films vus", nb_vus, border=True)
    with wishlist:
        st.metric("Films à voir", nb_wishlist, border=True)


    # --- Formulaire de Recherche ---
    _, form, _ = st.columns([1, 2, 1])
    with form:
        with st.form(key="search_form", enter_to_submit=False):
            query_movie = st.text_input(
                "Tapez votre recherche par titre", 
                key="input_movie"
            )

            query_actor = st.text_input(
                "Tapez votre recherche par acteur (séparés par des virgules)",
                key="input_actor"
            )

            col_sub, col_clr = st.columns(2)
            with col_sub:
                submit_button = st.form_submit_button(
                    label="Rechercher", use_container_width=True
                )
            with col_clr:
                clear_button = st.form_submit_button(
                    label="Effacer", use_container_width=True, on_click=clear_form_callback
                )

        if submit_button:
            st.session_state.movie_query = query_movie
            st.session_state.actor_query = query_actor
            
            clean_movie = [m.strip().lower() for m in query_movie.split(",") if m.strip()]
            actor_names = [a.strip().lower() for a in query_actor.split(",") if a.strip()]

            # --- FILTRAGE DE LA RECHERCHE ---
            pattern = "|".join([re.escape(str(x).lower().strip()) for x in clean_movie])
            
            # Cas A : Recherche uniquement par ACTEUR(S)
            if actor_names and not clean_movie:
                result = load_actors(actor_names)

            # Cas B : Recherche uniquement par TITRE DE FILM
            elif clean_movie and not actor_names:
                result = movies[
                    movies["french_title"].str.lower().str.contains(pattern, na=False)
                    | movies["original_title"].str.lower().str.contains(pattern, na=False)
                ]

            # Cas C : Combinaison TITRE + ACTEUR(S)
            elif clean_movie and actor_names:
                act = load_actors(actor_names)
                if not act.empty:
                    result = act[
                        act["french_title"].str.lower().str.contains(pattern, na=False) 
                        | act["original_title"].str.lower().str.contains(pattern, na=False)]
                else:
                    result = pd.DataFrame()

            # Cas D : Aucun champ rempli
            else:
                result = st.session_state.get("search_result", pd.DataFrame())

            st.session_state.search_result = result
            st.session_state.status = 'search'

        else:
            # Récupération du dernier résultat connu
            result = st.session_state.get("search_result", pd.DataFrame())

        # --- Affichage des Résultats ---
        if not result.empty:
            checked_movies = {}
            for idx, row in result.iterrows():
                # Attention : les clés des checkbox doivent être uniques
                checked_movies[row["movie_id"]] = st.checkbox(
                    f"{row['french_title']} ({row['original_title']}) - IMDb: {row['movie_id']}  -  {row['year']}",
                    key=f"chk_{row['movie_id']}",
                )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Marquer sélection comme Vu"):
                    selected = [mid for mid, checked in checked_movies.items() if checked]
                    if not selected:
                        show_message("Sélectionnez au moins un film.", message_type="warning")
                    else:
                        if update_user_movies(selected, saw_val=1, wishlist_val=0):
                            show_message(f"{len(selected)} film(s) marqué(s) comme Vu", message_type="success")
                            st.session_state.status = 'start'
                            time.sleep(1.5)
                            st.rerun()

            # Bouton : Ajouter sélection à la wishlist
            with col2:
                if st.button("Ajouter sélection à la wishlist"):
                    selected = [mid for mid, checked in checked_movies.items() if checked]
                    if not selected:
                        show_message("Sélectionnez au moins un film.", message_type="warning")
                    else:
                        if update_user_movies(selected, saw_val=0, wishlist_val=1):
                            show_message(f"{len(selected)} film(s) ajouté(s) à la wishlist", message_type="success")
                            st.session_state.status = 'start'
                            time.sleep(1.5)
                            st.rerun()

        else:
            if st.session_state.get("status") == 'search':
                show_message("Aucun résultat pour cette recherche.", message_type="info")