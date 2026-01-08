from sqlalchemy import create_engine
import streamlit as st
import pandas as pd
import psycopg2
import time



def get_connection(): 
    try: 
        return psycopg2.connect( database="leo_cinema_db", 
                                user='postgres', 
                                password='postgres', 
                                host='localhost', 
                                port='5432', options="-c client_encoding=latin1" ) 
    except Exception as e: 
        st.error(f"Erreur connexion BD : {e}") 
        return None


def load_movies(): 
    conn = get_connection() 
    if conn is None: 
        return pd.DataFrame() 
    
    df = pd.read_sql("SELECT * FROM movies", conn) 
    conn.close() 
    return df


def load_users():
    try:
        return pd.read_csv("../db_backup/user_list_db.csv", sep=";")
    except Exception as e:
        st.error(f"Erreur chargement CSV : {e}")
        return pd.DataFrame()

def refresh_data():
    st.session_state.movies = load_movies()
    st.session_state.users = load_users()

if 'movies' not in st.session_state:
    st.session_state.movies = load_movies()
if 'users' not in st.session_state:
    st.session_state.users = load_users()
if 'search_query' not in st.session_state:
    st.session_state.search_query = ''
if 'search_result' not in st.session_state:
    st.session_state.search_result = pd.DataFrame()

movies = st.session_state.movies
users = st.session_state.users

movies[["french_title", "original_title"]] = movies[["french_title", "original_title"]].astype(str)
movies["search_fr"] = movies["french_title"].str.lower()
movies["search_or"] = movies["original_title"].str.lower()

st.title("🎬 Recherche et mise à jour des films")

nb_vus = st.session_state.users["saw"].sum() if not st.session_state.users.empty else 0
nb_wishlist = st.session_state.users["wishlist"].sum() if not st.session_state.users.empty else 0

st.markdown(f"**Films vus :** {nb_vus}  |  **Films à voir (wishlist) :** {nb_wishlist}")

query = st.text_input("Tapez votre recherche", value=st.session_state.search_query)

if st.button("Rechercher"):
    st.session_state.search_query = query
    result = movies[(movies["search_fr"].str.contains(query.lower())) | (movies["search_or"].str.contains(query.lower()))]
    st.session_state.search_result = result
else:
    result = st.session_state.search_result

if not result.empty:
    checked_movies = {}
    for idx, row in result.iterrows():
        checked_movies[row["movie_id"]] = st.checkbox(
            f"{row['french_title']} ({row['original_title']}) - IMDb: {row['movie_id']}  -  {row['year']}", 
            key=f"chk_{row['movie_id']}"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Marquer sélection comme Vu"):
            selected = [mid for mid, checked in checked_movies.items() if checked]
            if not selected:
                st.warning("Sélectionnez au moins un film.")
            else:
                conn = get_connection()
                if conn is None:
                    st.error("Erreur connexion BD")
                else:
                    cursor = conn.cursor()
                    for code in selected:
                        try:
                            cursor.execute(
                                "UPDATE user_list SET saw = '1', wishlist = '0' WHERE movie_id = %s",
                                (code,)
                            )
                            users.loc[users["movie_id"] == code, ["saw", "wishlist"]] = [1, 0]
                        except Exception as e:
                            st.error(f"Erreur SQL sur {code}: {e}")
                    conn.commit()
                    cursor.close()
                    conn.close()

                    users.to_csv("../db_backup/user_list_db.csv", sep=";", index=False)
                    refresh_data()
                    st.success(f"{len(selected)} film(s) marqué(s) comme Vu")
                    time.sleep(2)
                    st.rerun()

    with col2:
        if st.button("Ajouter sélection à la wishlist"):
            selected = [mid for mid, checked in checked_movies.items() if checked]
            if not selected:
                st.warning("Sélectionnez au moins un film.")
            else:
                conn = get_connection()
                if conn is None:
                    st.error("Erreur connexion BD")
                else:
                    cursor = conn.cursor()
                    for code in selected:
                        try:
                            cursor.execute(
                                "UPDATE user_list SET saw = '0', wishlist = '1' WHERE movie_id = %s",
                                (code,)
                            )
                            users.loc[users["movie_id"] == code, ["saw", "wishlist"]] = [0,1]
                        except Exception as e:
                            st.error(f"Erreur SQL sur {code}: {e}")
                    conn.commit()
                    cursor.close()
                    conn.close()

                    users.to_csv("../db_backup/user_list_db.csv", sep=";", index=False)
                    refresh_data()
                    st.success(f"{len(selected)} film(s) ajouté(s) à la wishlist")
                    time.sleep(2)
                    st.rerun()
else:
    if st.session_state.search_query:
        st.warning("Aucun résultat pour cette recherche.")
