import streamlit as st
import pandas as pd
from src.config.settings import DATA_DIR
from src.services.db_connect import refresh_data


def update_user_movies(selected_ids, saw_val, wishlist_val):
  """Fonction helper pour mettre à jour la base de données et le session state."""
  try:
    conn = st.connection("postgresql", type="sql")
    users = st.session_state.users

    # st.connection gère un gestionnaire de contexte (with) pour les écritures
    # On récupère l'accès au moteur sous-jacent avec .connect()
    with conn.connect() as connection:
      for code in selected_ids:
        # En SQLAlchemy / st.connection, on utilise des paramètres nommés ou text()
        # Mais pour faire simple avec une requête textuelle brute :
        from sqlalchemy import text

        connection.execute(
            text(
                "UPDATE user_list SET saw = :saw, wishlist = :wishlist WHERE"
                " movie_id = :code"
            ),
            {"saw": str(saw_val), "wishlist": str(wishlist_val), "code": code},
        )
        users.loc[users["movie_id"] == code, ["saw", "wishlist"]] = [
            saw_val,
            wishlist_val,
        ]

      # Le commit est automatique à la sortie du bloc 'with' si tout va bien,
      # ou on peut l'exécuter explicitement selon la version du driver :
      connection.commit()

    # Backup CSV & Refresh (chemins ajustés si besoin selon l'emplacement de src)
    users.to_csv(DATA_DIR / "db_backup" / "user_list_db.csv", sep=";", index=False)
    refresh_data()
    return True

  except Exception as e:
    st.error(f"Erreur SQL : {e}")
    return False


def clear_form_callback():
    st.session_state.input_movie = ""
    st.session_state.input_actor = ""
    st.session_state.movie_query = ""
    st.session_state.actor_query = ""
    st.session_state.search_result = pd.DataFrame()
    st.session_state.status = "start"