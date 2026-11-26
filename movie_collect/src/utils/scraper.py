from bs4 import BeautifulSoup
import re
import pandas as pd
import json
import time
import random


from src.config.settings import DATA_DIR, EXCHANGER, SCRAPED_COLUMNS, UNION_COLUMNS, DIR_PROD_DICT


def parse_json_ld(soup):
    script_tag = soup.find('script', {'type': 'application/ld+json'})
    try:
        return json.loads(script_tag.string) if script_tag else {}
    except:
        return {}


def parse_duration(duration_str):
    if not duration_str: return 0
    duration = str(duration_str).replace("PT", "")
    hours = int(duration.split("H")[0]) if "H" in duration else 0
    minutes_part = duration.split("H")[1] if "H" in duration else duration
    minutes = int(minutes_part.split("M")[0]) if "M" in duration else 0
    return hours * 60 + minutes


def get_production_info(soup):
    companies = soup.find_all('a', {'href': re.compile('company')})
    
    if not companies:
        return [], []
        
    if "Production compan" not in companies[0].text:
        prod_names = []
    else:
        prod_names = [c.text for c in companies if "IMDbPro" not in c.text and c.text != "" and "Production compan" not in c.text]
        
    prod_codes = [str(c).split("company/")[1].split("/?ref")[0] for c in companies if "company/" in str(c)]
        
    return prod_names, prod_codes


def get_cast_and_director(soup):
    cast_names = []
    cast_codes = []
    cast_voice = []
    directors = []
    dir_codes = []

    persons = ["Cast","Director"]

    for person in persons:
        cast_title = soup.find(lambda tag: tag.name == "h3" and person in tag.get_text())
        if cast_title:
            cast_section = cast_title.find_parent("section")
            if cast_section:
                cast_items = cast_section.find_all("li", {"data-testid": "name-credits-list-item"})
                for item in cast_items:
                    person_link = item.find("a", class_="ipc-link ipc-link--base name-credits--title-text name-credits--title-text-big")
                    if person_link:
                        person_name = person_link.get_text(strip=True)
                        href = person_link.get("href", "")
            
                        # Code IMDb (nm...)
                        match = re.search(r"nm\d+", href)
                        person_code = match.group(0) if match else None
            
                        if person_code and person == "Cast":
                            # 2. Extraction du type (Voice / Uncredited / Aucun)
                            # On récupère tout le texte de la zone de métadonnées du personnage
                            metadata_div = item.find("div", class_="sc-ed2abe21-7 hujYBw")
                            metadata_text = (metadata_div.get_text().lower() if metadata_div else "")
        
                            if "voice" in metadata_text:
                                voice_type = "V"
                            elif "uncredited" in metadata_text:
                                voice_type = "U"
                            else:
                                voice_type = "A"
        
                            cast_names.append(person_name)
                            cast_codes.append(person_code)
                            cast_voice.append(voice_type)
                        elif person_code and person == "Director":
                            directors.append(person_name)
                            dir_codes.append(person_code)
    
    if len(cast_names) > 30:
        cast_names, cast_codes, cast_voice = cast_names[:30], cast_codes[:30], cast_voice[:30]

    return cast_names, cast_codes, cast_voice, directors, dir_codes



# --- FONCTION PRINCIPALE ---

def movie_imdb_full_logic(driver, imdb_id, french_title):
    
    # 1. PAGE PRINCIPALE (Infos, Budget, Directors)
    url_main = f"https://www.imdb.com/title/{imdb_id}/?language=en-US"
    driver.get(url_main)
    time.sleep(random.uniform(4, 6))
        
    soup_main = BeautifulSoup(driver.page_source, "html.parser")
    info_main = parse_json_ld(soup_main)
        
    # 2. PAGE FULL CREDITS (Pour avoir le Top 30)
    url_credits = f"https://www.imdb.com/title/{imdb_id}/fullcredits?language=en-US"
    driver.get(url_credits)
    time.sleep(random.uniform(3, 5))
        
    soup_credits = BeautifulSoup(driver.page_source, "html.parser")

    # --- EXTRACTION ---0
    title = info_main.get("name", "").replace("&amp;", "&").replace("&apos;", "'")

    # Cast (depuis la fonction dédiée sur soup_credits)
    cast_names, cast_codes, cast_roles, directors, dir_codes = get_cast_and_director(soup_credits)

    # Le reste de la logique (Budget, Pays, Langues, Prods)
    # Budget

    budget, bud_currency = 0, ""

    try :
        budget_label = soup_main.find(lambda tag: tag.name == 'span' and tag.text.strip() == 'Budget')
        if budget_label:
            budget_value_span = budget_label.find_next(
                'span', 
                {'class': re.compile('ipc-metadata-list-item__list-content-item')}
            )
            if budget_value_span:
                budget_text = budget_value_span.text.strip()
                
            parts = budget_text.replace("\u202f", "").replace("\xa0", " ").split(" ")
    
            try:
                budget = int(parts[0][1:].replace(",",""))
                bud_currency = parts[0][0]
            except ValueError:
                budget = int(parts[1].replace(",",""))
                bud_currency = parts[0]
    except Exception:
        budget, bud_currency = 0, ""

    # Productions
    prod_names, prod_codes = get_production_info(soup_main)

    # Rating, Year, Genres, Pays, Langues
    rating = info_main.get("aggregateRating", {}).get("ratingValue", "")
    num_rate = info_main.get("aggregateRating", {}).get("ratingCount", "")

    year_m = re.search(r'\((\d{4})\)', soup_main.title.text)
    year = int(year_m.group(1)) if year_m else None

    duration = parse_duration(info_main.get("duration", ""))
    genres = info_main.get("genre", [])

    country = [c.text for c in soup_main.find_all('a', {'href': re.compile('country_of_origin')})] or ["No Info"]
    country = ["USA" if c == "United States" else "UK" if c == "United Kingdom" else c for c in country]
    language = [l.text for l in soup_main.find_all('a', {'href': re.compile('primary_language')})] or ["No Info"]

    return (
            imdb_id, french_title, title, year, directors, dir_codes, 
            cast_names, cast_codes, cast_roles, genres, duration, 
            country, language, prod_names, prod_codes, 
            rating, num_rate, budget, bud_currency
        )


def create_scrap_table(movie):
    movie_df = pd.DataFrame(movie,columns = SCRAPED_COLUMNS)
    movie_keep = movie_df.drop(movie_df[movie_df["rating"] == ""].index).reset_index(drop=True)
    too_soon = pd.DataFrame(movie_df[["movie_id","french_title"]]
                            .drop(movie_df[movie_df["rating"] != ""].index)
                            .values,
                            columns= ['imdb_id', 'title']).set_index("imdb_id")
    if len(too_soon) > 0:
        f_scrap = pd.read_csv(DATA_DIR / "too_soon.csv", encoding="ISO-8859-1", sep=";").set_index("imdb_id")
        too_soon = pd.concat([f_scrap, too_soon])
        too_soon.to_csv(DATA_DIR / "too_soon.csv", encoding="ISO-8859-1", sep=";")

    movie_keep["def_budget"] = movie_keep["budget"] * movie_keep["currency"].apply(lambda x : EXCHANGER[x] if x != "" else 1)
    movie_keep["def_budget"] = movie_keep["def_budget"].apply(lambda x: int(x) if x !=0 else "")

    for col in UNION_COLUMNS:
        movie_keep[f"{col}s"] = movie_keep[col].apply(lambda x : " | ".join(x))
    
    movie_keep["saw"] = False
    movie_keep["wishlist"] = False

    select = movie_keep[["movie_id","saw","wishlist","french_title","original_title",
                         "year","directors","actors","genres","duration","countrys",
                         "languages","productions","rating","num_rate","def_budget"]]

    select.to_excel(DATA_DIR / "movies_scraped.xlsx", index=False)

    return movie_keep, select


def update_movie_and_user(select, type):
    up_movies = select[["movie_id","french_title","original_title","year","duration","rating","num_rate","def_budget"]]\
        .set_index("movie_id").rename(columns = {"def_budget":"budget"})
    up_movies.to_csv(DATA_DIR / "update_db/up_movies.csv", encoding="utf-8-sig", sep=";")
    
    up_user = select[["movie_id","saw","wishlist"]].set_index("movie_id")
    if type == "unique":
        up_user["saw"] = True
        up_user["wishlist"] = False
    up_user.to_csv(DATA_DIR / "update_db/up_user.csv", encoding="utf-8-sig", sep=";")


def update_genre(movie_keep):
    genre_df = pd.read_csv(DATA_DIR / "db_backup/genres_db.csv", sep=";")
    genre_dict = dict(zip(genre_df["name"], genre_df["genre_id"]))
    genre_dict[""] = ""

    tot_genre_df = movie_keep[["movie_id","genre"]].explode(["genre"], ignore_index=True)
    tot_genre_df = tot_genre_df.fillna("")
    tot_genre_df["genre_id"] = tot_genre_df["genre"].apply(lambda x: genre_dict[x])
    tot_genre_df = tot_genre_df.drop(["genre"], axis=1).drop_duplicates()
    tot_genre_df = tot_genre_df[tot_genre_df["genre_id"].notna() & (tot_genre_df["genre_id"].astype(str).str.strip() != "")]

    tot_genre_df.set_index("movie_id").to_csv(DATA_DIR / "update_db/up_movie_genre.csv", sep=";")


def update_actors(movie_keep):
    tot_actor_df = movie_keep[["movie_id","actor", "actor_id", "status"]].explode(["actor", "actor_id", "status"], ignore_index=True)
    tot_actor_df["status"] = tot_actor_df["status"].str.replace("A", "", regex=False)
    tot_actor_final = tot_actor_df.drop(["actor"], axis=1).drop_duplicates()
    tot_actor_final = tot_actor_final[tot_actor_final["actor_id"].notna() & (tot_actor_final["actor_id"].str.strip() != "")]
    tot_actor_final.set_index("movie_id").to_csv(DATA_DIR / "update_db/up_movie_actor.csv", sep=";")

    act_db = pd.read_csv(DATA_DIR / f'db_backup/actors_db.csv', encoding="utf-8-sig", sep=";")

    actors_df = tot_actor_df.drop(["movie_id", "status"], axis=1).drop_duplicates()
    new_actors = actors_df[~actors_df["actor_id"].isin(act_db["actor_id"])]
    new_actors= new_actors[new_actors["actor_id"].notna() & (new_actors["actor_id"].str.strip() != "")]
    if len(new_actors) != 0:
        new_actors.columns = ["name","actor_id"]
        new_actors.set_index("actor_id").to_csv(DATA_DIR / "update_db/up_actor.csv", encoding="utf-8-sig", sep=";")


def update_director_production(movie_keep):
    for k, v in DIR_PROD_DICT.items():
        tot_df = movie_keep[["movie_id",v[0], v[1]]].explode([v[0], v[1]], ignore_index=True)
        tot_df_final = tot_df.drop([v[0]], axis=1).drop_duplicates()
        tot_df_final = tot_df_final[tot_df_final[v[1]].notna() & (tot_df_final[v[1]].str.strip() != "")]
        tot_df_final.set_index("movie_id").to_csv(DATA_DIR / f"update_db/up_movie_{k}.csv", sep=";")

        val_db = pd.read_csv(DATA_DIR / f'db_backup/{v[0]}_db.csv', encoding="utf-8-sig", sep=";")
        
        val_df = tot_df.drop(["movie_id"], axis=1).drop_duplicates()
        new_val = val_df[~val_df[v[1]].isin(val_db[v[1]])]
        new_val = new_val[new_val[v[1]].notna() & (new_val[v[1]] != "")]
        if len(new_val) != 0:
            new_val.columns = ["name",v[1]]
            new_val.set_index(v[1]).to_csv(DATA_DIR / f"update_db/up_{v[0]}.csv", encoding="utf-8-sig", sep=";")


def get_or_create_id(name, current_dict, max_val):
    if name not in current_dict:
        max_val[0] += 1
        current_dict[name] = max_val[0]
    return current_dict[name]


def update_country_language(movie_keep):
    for val in ["country", "language"]:
        try:
            val_db2 = pd.read_csv(DATA_DIR / f'db_backup/{val}_db.csv', encoding="ISO-8859-1", sep=";")
            info_dict = dict(zip(val_db2["name"], val_db2[f"{val}_id"]))
        except KeyError:
            val_db2 = pd.read_csv(DATA_DIR / f'db_backup/{val}_db.csv', encoding="utf-8-sig", sep=";")
            info_dict = dict(zip(val_db2["name"], val_db2[f"{val}_id"]))

        info_dict = { (None if pd.isna(k) else k): v for k, v in info_dict.items() }
        current_max_id = val_db2[f"{val}_id"].max()

        max_ref = [current_max_id]
        
        tot_df2 = movie_keep[["movie_id", val]].explode([val], ignore_index=True)
        tot_df2[f"{val}_id"] = tot_df2[val].apply(lambda x: get_or_create_id(x, info_dict, max_ref))
        tot_df2.columns = ["movie_id","name",f"{val}_id"]
        tot_df2_final = tot_df2.drop("name", axis=1).drop_duplicates()
        tot_df2_final = tot_df2_final[tot_df2_final[f"{val}_id"].notna() & (tot_df2_final[f"{val}_id"] != "")]
        tot_df2_final.set_index("movie_id").to_csv(DATA_DIR / f"update_db/up_movie_{val}.csv", encoding="utf-8-sig", sep=";")
        
        new_val2 = tot_df2[~tot_df2[f"{val}_id"].isin(val_db2[f"{val}_id"])]
        new_val2 = new_val2[new_val2[f"{val}_id"].notna() & (new_val2[f"{val}_id"] != "")]
        new_val2 = new_val2.drop(["movie_id"], axis=1).drop_duplicates()
        if len(new_val2) != 0:
            new_val2.set_index(f"{val}_id").to_csv(DATA_DIR / f"update_db/up_{val}.csv", encoding="utf-8-sig", sep=";")


