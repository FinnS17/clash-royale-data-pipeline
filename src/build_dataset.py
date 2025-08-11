import requests
import pandas as pd
pd.set_option("display.max_columns", None)
from api_config import HEADERS, MAX_RETRIES, BASE_URL
import time
import logging
import pathlib
import json

logger = logging.getLogger(__name__)

VISITED_PATH = pathlib.Path("checkpoints/visited_clans.json")
VISITED_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_visited_clans() -> set[str]:
    if not VISITED_PATH.exists():
        return set()
    try:
        data = json.loads(VISITED_PATH.read_text())
        return set(data)
    except Exception as e:
        logger.warning("could not load visited_clans: %s - start with 0 Clans", e)

def save_visited_clans(visited: set[str]) -> None:
    VISITED_PATH.write_text(json.dumps(sorted(visited)))
    logger.info("Visited-Clans-checkpoint updated (%d Einträge)", len(visited))


def save_parquet(df: pd.DataFrame, path: str) -> None:
    "Saves DF as Parquet-File"
    path_obj = pathlib.Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)  # Ordner erstellen, falls nicht vorhanden
    df.to_parquet(path_obj, index=False)
    logger.info("Parquet-Datei gespeichert: %s", path_obj)


def safe_request(url, headers):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                logger.warning("Rate limit! Waiting 10 seconds...")
                time.sleep(10)
            else:
                logger.warning("❗️Unexpected status code %s", response.status_code)
                return None
        except requests.exceptions.RequestException as e:
            logger.error("⚠️ Request failed %s", e)
            time.sleep(5)  # Warten und neu versuchen
    return None  # Nach max_retries None zurückgeben
        



def parse_battle(battle):
    try:
        player = battle["team"][0]
        opponent = battle["opponent"][0]
        opponent_deck = [card["name"] for card in opponent["cards"]]
        deck = [card["name"] for card in player["cards"]]
        trophies = player.get("startingTrophies", None)
        opponent_trophies = opponent.get("startingTrophies", None)
        crowns = player["crowns"]
        opponent_crowns = opponent["crowns"]
        result = 1 if crowns > opponent_crowns else 0
    

        return {
            "player_tag": player["tag"],
            "player_deck": deck,
            "player_trophies": trophies,
            "player_crowns": crowns,
            "opponent_tag": opponent["tag"],
            "opponent_clan": opponent.get("clan", {}).get("tag", None).replace("#", "") if opponent.get("clan") else None,
            "opponent_crowns": opponent_crowns,
            "opponent_trophies": opponent_trophies,
            "opponent_deck": opponent_deck,
            "result": result,           
        }
    except Exception as e:
        logger.error("Error parsing battle %s", e)
        return None

def get_clan_members(clan_tag):
    url = f"{BASE_URL}/clans/%23{clan_tag}/members"
    response = safe_request(url, headers=HEADERS)
    if response is None:
        logger.warning("⚠️ Keine Antwort für Clan %s", clan_tag)
        return []
    try:
        members = response.json()["items"]
        player_tags = [member["tag"][1:] for member in members]
        return player_tags
    except Exception as e:
        logger.error("❌ Fehler beim Verarbeiten der Clanmitglieder: %s", e)
        return []

   
def get_battles_for_player(player_tag):
    url = f"{BASE_URL}/players/%23{player_tag}/battlelog"
    response = safe_request(url, headers=HEADERS)

    if response is None:
        logger.warning("⚠️ Keine Antwort für Spieler %s", player_tag)
        return []

    try:
        battles = response.json()
        parsed_battles = []
        for battle in battles:
            if battle.get("gameMode", {}).get("name") == "Ladder":
                parsed = parse_battle(battle)
                if parsed:
                    parsed_battles.append(parsed)
        return parsed_battles
    except Exception as e:
        logger.error("❌ Fehler beim Verarbeiten der Battles von Spieler %s: %s", player_tag, e)
        return []
            
           
def build_dataset_for_clan(clan_tag):
    all_parsed_battles = []
    player_tags = get_clan_members(clan_tag)
    logger.info("%d Playertags verarbeiten von Clan %s...", len(player_tags), clan_tag)
    for tag in player_tags:
        battles = get_battles_for_player(tag)
        if battles:
            all_parsed_battles.extend(battles)
    df = pd.DataFrame(all_parsed_battles)

    new_rows = []
    for i, row in df.iterrows():
        flipped = {
            "player_tag": row["opponent_tag"],
            "player_deck": row["opponent_deck"],
            "player_trophies": row["opponent_trophies"],
            "player_crowns": row["opponent_crowns"],
            "opponent_tag": row["player_tag"],
            "opponent_clan": None,
            "opponent_crowns": row["player_crowns"],
            "opponent_trophies": row["player_trophies"],
            "opponent_deck": row["player_deck"],
            "result": 0 if row["result"] == 1 else 1,
        }
        new_rows.append(flipped)
    df_flipped = pd.DataFrame(new_rows)
    df = pd.concat([df, df_flipped], ignore_index= True)
    logger.info("Ingesamt %d Spiele gesammelt", len(df))
    return df

def discover_and_expand(df, max_new_clans, visited_clans: set[str]):
    potential_clans = df["opponent_clan"].dropna().unique()
    new_clans = [c for c in potential_clans if c not in visited_clans][:max_new_clans]
    logger.info("Neue gefundene Clans %s", new_clans)
    all_new_data = []
    for i, clan_tag in enumerate(new_clans):
        logger.info("🔍 Hole Daten für neuen Clan: %s", clan_tag)
        new_df = build_dataset_for_clan(clan_tag)
        if new_df is not None and not new_df.empty:
            all_new_data.append(new_df)
            visited_clans.add(clan_tag)
            save_visited_clans(visited_clans)

    if all_new_data:
        df = pd.concat([df] + all_new_data, ignore_index=True)
    return df, visited_clans

def build_complete_dataset(clan_tag, max_new_clans):
    path = pathlib.Path("data/clash_battles.parquet")
    if path.exists():
        logger.info("found existing Data - load %s", path)
        df = pd.read_parquet(path)
    else: 
        logger.info("no existing data found - start new")
        df = build_dataset_for_clan(clan_tag)
    visited = load_visited_clans()
    expanded_df, visited = discover_and_expand(df, max_new_clans, visited)
    logger.info("%d Battles gescraped", len(expanded_df))
    save_parquet(expanded_df, "data/clash_battles.parquet")
    save_visited_clans(visited)
    logger.info("✅ Finaler Datensatz gespeichert & visited clans actualisiert.")






