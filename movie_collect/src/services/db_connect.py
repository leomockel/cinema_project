import streamlit as st
import pandas as pd
from src.config.settings import DATA_DIR



# 1. Chargement des films (le paramètre `ttl` gère le cache automatiquement)
@st.cache_data(ttl=600, show_spinner=False)
def load_movies():
    conn = st.connection("postgresql", type="sql")
    return conn.query("SELECT * FROM movies;", ttl=600)


# 2. Chargement des utilisateurs (reste en CSV)
@st.cache_data(ttl=600, show_spinner=False)
def load_users():
    try:
      return pd.read_csv(
          DATA_DIR / "db_backup" / "user_list_db.csv", sep=";"
      )
    except Exception as e:
      st.error(f"Erreur chargement CSV : {e}")
      return pd.DataFrame()


# 3. Chargement des acteurs avec recherche dynamique sécurisée
@st.cache_data(ttl=600, show_spinner=False)
def load_actors(name):
    if isinstance(name, list):
      names = [
          val.strip().lower()
          for val in name
          if isinstance(val, str) and val.strip()
      ]
    elif isinstance(name, str):
      names = [val.strip().lower() for val in name.split(",") if val.strip()]
    else:
      names = []

    if not names:
      return pd.DataFrame()

    # Construction dynamique des paramètres nommés pour SQLAlchemy
    # Exemple : name_0, name_1, etc.
    like_clauses = []
    having_clauses = []
    params = {}

    for i, n in enumerate(names):
      param_key = f"n_{i}"
      like_clauses.append(f"LOWER(a.name) LIKE :{param_key}")
      having_clauses.append(
          f"COUNT(DISTINCT CASE WHEN LOWER(a.name) LIKE :{param_key} THEN 1 END) >"
          " 0"
      )
      params[param_key] = f"%{n}%"

    query = f"""
          SELECT m.movie_id, m.french_title, m.original_title, m.year
          FROM movies m
          JOIN movie_actor ma ON m.movie_id = ma.movie_id
          JOIN actors a ON ma.actor_id = a.actor_id
          WHERE {" OR ".join(like_clauses)}
          GROUP BY m.movie_id, m.french_title, m.original_title, m.year
          HAVING {" AND ".join(having_clauses)}
      """

    # Exécution sécurisée via st.connection avec le dictionnaire de paramètres
    conn = st.connection("postgresql", type="sql")
    df = conn.query(query, params=params, ttl=600)
    return df
    

def refresh_data():
    load_movies.clear()
    load_users.clear()
    
    st.session_state.movies = load_movies()
    st.session_state.users = load_users()


