from pathlib import Path
import pandas as pd

# Chemins du projet
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
DATA_DIR = STATIC_DIR / "data"
IMAGES_DIR = STATIC_DIR / "images"

# Configuration Streamlit
PAGE_CONFIG = {
    "page_title": "Movie Collector",
    "page_icon": ":movie_camera:",
    "layout": "wide",
}

# Métadonnées de l'app
APP_INFO = {
    "title": "Movie Collector",
    "description": "Application to update the list of your movies seen",
    "version": "1.0.0",
    "author": "Lionel Mockel"
}


SESSION_DICT = {
    "status": "start",
    "movie_query": "",
    "actor_query": "",
    "search_result": pd.DataFrame(),
    "search_counter": 0,
}


HEADER_STYLES = {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
      'Accept-Charset': 'ISO-8859-1,latin-1;q=0.7,*;q=0.3',
      'Accept-Encoding': 'none',
      'Accept-Language': 'fr;q=0.9,en-US,en;q=0.8',
      'Connection': 'keep-alive',
      'referer': 'https://imdb.com'
}


DB_UPDATE_DICT = {
    "movies_db":["up_movies", "movie_id", "movies"],
    "actors_db":["up_actor", "actor_id", "actors"],
    "country_db":["up_country", "country_id", "country"],
    "director_db":["up_director", "director_id","directors"],
    "genres_db":["up_genre", "genre_id", "genres"],
    "language_db":["up_language", "language_id", "language"],
    "production_db":["up_production", "prod_id", "production"],
    "movie_actor_db_2":["up_movie_actor", "movie_id", "movie_actor"],
    "movie_country_db":["up_movie_country", "movie_id", "movie_country"],
    "movie_dir_db":["up_movie_dir", "movie_id", "movie_director"],
    "movie_genre_db":["up_movie_genre", "movie_id", "movie_genre"],
    "movie_language_db":["up_movie_language", "movie_id", "movie_language"],
    "movie_prod_db":["up_movie_prod", "movie_id", "movie_prod"],
    "user_list_db":["up_user", "movie_id", "user_list"]
}


EXCHANGER = {"$US":1, "$":1, "$CA":0.72, "$AU":0.65, "€":1.08, "£GB":1.29, "₩":0.00073, "₹":0.012, "CNY":0.14, "RUR":0.011,
             "CZK":0.043, "NOK":0.092, "BDT":0.0085, "HKD":0.13, "R$":0.162, "CHF":0.8, "MYR":0.24}


DIR_PROD_DICT = {"dir":["director","director_id"],"prod":["production","prod_id"]}


NEW_ORDER = ["week", "imdb_id", "query", "director", "actor", "act_match", "year", "similarity", "extract_title"]

SCRAPED_COLUMNS = ["movie_id","french_title","original_title","year","director","director_id",
                   "actor","actor_id","status","genre","duration","country","language","production",
                   "prod_id","rating","num_rate","budget","currency"]

UNION_COLUMNS = ["actor","country","director","genre","language","production"]