import streamlit as st
import pandas as pd
import sqlalchemy as db
import psycopg2
import os
from dotenv import load_dotenv

from src.components.UX_helper import apply_page_styles, show_message
from src.config.settings import IMAGES_DIR, NEW_ORDER, DB_UPDATE_DICT, DATA_DIR
from src.services.process import refresh_data
from src.services.process import clear_form_callback
from src.utils.digger import get_month_movies, get_similar_movies
from src.utils.drive_tools import get_chrome_version_windows, init_driver
from src.utils.scraper import movie_imdb_full_logic, create_scrap_table, update_actors, update_country_language, update_country_language, update_director_production, update_movie_and_user, update_genre


def scrap_page():
    # 1. On applique le fond et les CSS spécifiques à CETTE page dès son chargement
    apply_page_styles(
        bg_image_path=IMAGES_DIR / "matrix_wallpaper.jpg", 
        css_files=["src/styles/themes.css", "src/styles/scrap_components.css"]
    )

    # 2. Le reste de votre page s'exécute normalement
    st.markdown(
        "<div style='text-align: center;'><h1 class='custom-header'>🎬 Récupérer les données de films sur imdb</h1></div>", 
        unsafe_allow_html=True
    )

    _, tabs_col, _ = st.columns([1, 2, 1])
    with tabs_col:
        tab_batch, tab_single = st.tabs(["Récupération du mois", "Récupération ponctuelle"])
        with tab_batch:
            # --- Formulaire de Recherche ---
            with st.form(key="month_form", enter_to_submit=False):
                col1, col2 = st.columns(2)
        
                with col1:
                    month = st.text_input(
                        "Mois", 
                        key="input_month"
                    )

                with col2:
                    year = st.text_input(
                        "Année",
                        key="input_year"
                    )

                _, search_col, _, clear_col, _ = st.columns([1, 2, 2, 2, 1])

                with search_col:
                    search_button = st.form_submit_button(
                        label="Rechercher", width="stretch"
                    )

                with clear_col  :
                    clear_button = st.form_submit_button(
                        label="Effacer", width="stretch", on_click=clear_form_callback
                    )

            if search_button:
                st.session_state.month = month
                st.session_state.year = year

                month_movies = get_month_movies(int(year), month)
                chrome_version = get_chrome_version_windows()
                st.session_state.chrome_version = chrome_version
                driver = init_driver(st.session_state.chrome_version)
                try:
                    total_results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    total_rows = len(month_movies)

                    for index, row in month_movies.iterrows():
                        status_text.text(f"Traitement en cours ({index + 1}/{total_rows})...")
                        df_res = get_similar_movies(driver, row.to_dict(), is_global=True)
                        if not df_res.empty:
                            total_results.append(df_res)
                        progress_bar.progress((index + 1) / total_rows)

                    status_text.success("Traitement terminé avec succès !")
                    progress_bar.empty()

                    if total_results:
                        df_final = pd.concat(total_results, ignore_index=True)
                        new_df = pd.merge(month_movies, df_final, left_on="title", right_on="query", how="left")
                        new_df = new_df[NEW_ORDER]
                        new_df.to_excel(DATA_DIR / "new_movies.xlsx", index=False)
                finally:
                    driver.quit()  # Fermeture garantie du navigateur

            if clear_button:
                clear_form_callback()
                st.session_state.month = ""
                st.session_state.year = ""

    with tab_single:
        # --- Formulaire de Recherche ---
        with st.form(key="single_form", enter_to_submit=False):
            movie_single = st.text_input(
                "Taper le titre du film", 
                key="input_title"
            )

            _, search_col, _, clear_col, _ = st.columns([1, 2, 2, 2, 1])

            with search_col:
                search_button = st.form_submit_button(
                    label="Rechercher", width="stretch"
                )

            with clear_col:
                clear_button = st.form_submit_button(
                    label="Effacer", width="stretch", on_click=clear_form_callback
                )

        if search_button:
            st.session_state.df_res = pd.DataFrame()
            st.session_state.selected_index = None
            st.session_state.search_counter += 1  # Incrémente le compteur de recherche

            if movie_single.strip() == "":
                show_message("Ecrire un titre de film", "warning")
            else:
                st.session_state.movie_single = movie_single

                chrome_version = get_chrome_version_windows()
                st.session_state.chrome_version = chrome_version
                driver = init_driver(st.session_state.chrome_version)


                try:
                    df_res = get_similar_movies(driver, pd.DataFrame({"title": [movie_single], "actor": [""]}))
                    st.session_state.df_res = df_res
                finally:
                    driver.quit()

        # On vérifie si le dataframe existe en session
        if "df_res" in st.session_state and not st.session_state.df_res.empty:
            event = st.dataframe(
                st.session_state.df_res,
                on_select="rerun",
                selection_mode="single-row",
                key=f"movie_dataframe_{st.session_state.search_counter}"
            )
            
            selected_rows = event.selection.rows
            if selected_rows:
                st.session_state.selected_index = selected_rows[0]

        # --- 2. GESTION DE LA LIGNE SÉLECTIONNÉE ET DU BOUTON DE SCRAPING ---
        # On vérifie si un index a bien été stocké en mémoire
            selected_index = st.session_state.selected_index
            if selected_index is not None:
                selected_row_data = st.session_state.df_res.iloc[selected_index]
                    
                # Affichez les clés disponibles pour être sûr de la colonne à cibler (ex: 'title', 'id', etc.)
                with st.container(border=False):
                    st.markdown(
                        f"""
                        <div class="movie-to-fetch">
                            <div class="movie-to-fetch-label">Film à récupérer</div>
                            <div class="movie-to-fetch-info">
                                {selected_row_data['extract_title']} |
                                {selected_row_data['imdb_id']} |
                                {selected_row_data['year']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                
                
                # Le bouton de scraping
                if st.button("Lancer le scraping de cette ligne"):
                    target_value = selected_row_data.get("imdb_id", "Valeur par défaut")
                    driver = init_driver(st.session_state.chrome_version)

                    try:
                        single_movie = [movie_imdb_full_logic(driver, selected_row_data['imdb_id'], selected_row_data['extract_title'])]
                    finally :
                        driver.quit()

                    movie_keep, select = create_scrap_table(single_movie)
                    update_movie_and_user(select, "unique")
                    update_genre(movie_keep)
                    update_actors(movie_keep)
                    update_director_production(movie_keep)
                    update_country_language(movie_keep)

                    load_dotenv()

                    DATABASE_URL = os.getenv("DATABASE_URL")
                    engine = db.create_engine(DATABASE_URL)

                    with engine.begin() as connection:
                        for key, value in DB_UPDATE_DICT.items():
                            update_file_path = DATA_DIR / f"update_db/{value[0]}.csv"
                            print(f"Processing {update_file_path} for table {value[2]}...")          
                            if os.path.isfile(update_file_path):
                                database = pd.read_csv(DATA_DIR / f"db_backup/{key}.csv", encoding="utf-8-sig", sep=";").set_index(value[1])
                                up = pd.read_csv(update_file_path, encoding="utf-8-sig", sep=";").set_index(value[1])
                               
                                # Injection sécurisée avec la connexion transactionnelle
                                up.to_sql(value[2], con=connection, if_exists="append")
                                
                                # Mise à jour du backup local
                                pd.concat([database, up]).to_csv(DATA_DIR / f"db_backup/{key}.csv", encoding="utf-8-sig", sep=";")

                    show_message("Update finished successfully!", message_type="success")
                    refresh_data()