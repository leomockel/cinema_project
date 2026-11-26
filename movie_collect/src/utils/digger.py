from bs4 import BeautifulSoup
import pandas as pd
from urllib.request import Request, urlopen
from urllib.parse import quote
import re
from difflib import SequenceMatcher
import time
import random
from datetime import datetime


from src.config.settings import HEADER_STYLES


def date_convertor(date_str):
    # Dictionnaire des mois en français
    month_fr = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
    }
    
    # Nettoyage de la chaîne (minuscules, suppression des espaces superflus)
    parts = date_str.strip().lower().split()
    
    day = int(parts[0])
    month = month_fr.get(parts[1])
    year = int(parts[2])
        
    dt = datetime(year, month, day)
    return dt.strftime('%Y-%m-%d')


def get_month_movies(year, month):

    month_dict = {'january':'01', 'february':'02', 'march':'03', 'april':'04', 'may':'05', 'june':'06', \
                'july':'07', 'august':'08', 'september':'09', 'october':'10', 'november':'11', 'december':'12'}

    req1 = Request(f"https://www.allocine.fr/film/agenda/mois/mois-{year}-{month_dict[month]}", headers=HEADER_STYLES)
    webpage1 = urlopen(req1).read()
    bs = BeautifulSoup(webpage1, "html.parser")

    results = []
    blocks = bs.find_all('div', class_='movie-agenda-month')

    for block in blocks:
        # 1. On récupère le titre (h2) de la semaine
        h2 = block.find('h2', class_='title-inter')
        if h2:
            week = date_convertor(h2.get_text(strip=True).replace("Films sortis en salles la semaine du ",""))
        
        # 2. On récupère tous les films (li) à l'intérieur de ce bloc
        li_films = block.find_all('li', class_='month-movie-item')
        
        for li in li_films:
            a_tag = li.find('a', class_='month-movies-link')
            if a_tag:
                title = a_tag.get_text(strip=True)
                spans = li.find_all('span', class_='light')
                try :
                    if len(spans) > 1:
                        director = spans[0].get_text().split("De\n")[1]
                        director = re.sub(r'\s+', ' ', director).strip()
                        actors = spans[2].get_text().split("Avec\n")[1]
                        actors = re.sub(r'\s+', ' ', actors).strip()
                    else : 
                        director = spans[0].get_text().split("De\n")[1]
                        director = re.sub(r'\s+', ' ', director).strip()
                        actors = ""
                except IndexError:
                    director = ""
                    actors = ""
                        
                results.append({
                    'week': week,
                    'title': title,
                    'director': director,
                    'actor': actors
                })
                
    month_movies = pd.DataFrame(results)

    return month_movies


def get_similar_movies(driver, row: dict[str, str], is_global: bool = False) -> pd.DataFrame:
    # Nettoyage simplifié de la query (on garde l'essentiel)
    query_clean = str(row["title"].iloc[0]).strip()
    
    # Encodage propre de l'URL (gère les espaces, accents, caractères spéciaux)
    # Cela remplace avantageusement votre 'char_dict'
    query_encoded = quote(query_clean)
    url_main = f"https://www.imdb.com/find/?s=tt&q={query_encoded}&ref_=nv_sr_sm"
    
    driver.get(url_main)
    # Temps d'attente pour le rendu JS
    time.sleep(random.uniform(3, 5))
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Sélecteur plus précis pour les lignes de résultats
    items = soup.select('li.ipc-metadata-list-summary-item')[:6]
    
    results = []
    
    for li_tag in items:
        # 1. Extraction du Titre et de l'ID IMDb
        # On cherche le lien qui contient le titre
        link_tag = li_tag.select('a')[-1]
        if not link_tag:
            continue
            
        title = link_tag.get_text(strip=True)
        href = link_tag.get('href', '')
        
        # Extraction ID (ex: tt1234567)
        match_id = re.search(r'tt\d+', href)
        imdb_id = match_id.group() if match_id else ""

        # 2. Chercher acteurs pour vérifier la correspondance
        actor_search = str(li_tag.select('div.ipc-media')[0])
        actor_val = row["actor"].iloc[0] if hasattr(row["actor"], "iloc") else row["actor"]

        if actor_val != "" and actor_val != [""] and actor_val is not None:
            act_match = round(sum([1 for actor in row["actor"].split(", ") if actor in actor_search]) / len(row["actor"].split(", ")) * 100,2)
        else:
            act_match = 0

        # 3. Extraction de l'année
        year_info = li_tag.select('div.ipc-media')
        year = 1492
        for span in year_info:
            match = re.search(r'\d{4}', str(span))
            if match:
                year = int(match.group())
                break
        
        # 3. Calcul de similarité
        similarity = SequenceMatcher(None, query_clean.lower(), title.lower()).ratio()
        
        # Filtrage selon vos critères (Année > 2022 et similitude > 0.6)
        if similarity >= 0.6 and (not is_global or year > 2022):
            results.append({
                "imdb_id": imdb_id,
                "extract_title": title,
                "act_match": act_match,
                "query": query_clean,
                "year": year,
                "similarity": round(similarity, 3)
            })

    # Gestion du cas vide
    if not results:
        results = [{"imdb_id": "", "extract_title": "", "act_match": "", "query": query_clean, "year": "", "similarity": ""}]

    final_df = pd.DataFrame(results)
    if not is_global:
        final_df = final_df.drop(["act_match"], axis=1)

    return final_df

