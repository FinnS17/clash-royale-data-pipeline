"""
Data collection utilities for Clash Royale battles.

This module handles:
- Loading/saving a checkpoint of visited clans
- Robust HTTP GET with simple retry and rate-limit handling
- Parsing battle logs into a tabular structure
- Building a battle dataset for a given clan
- Expanding the dataset by discovering opponent clans
- Persisting the final dataset to Parquet
"""

import requests
import pandas as pd
pd.set_option("display.max_columns", None)

from api_config import HEADERS, MAX_RETRIES, BASE_URL  # config values
import time
import logging
import pathlib
import json
from typing import List, Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Checkpoint file for visited/expanded clan tags
VISITED_PATH = pathlib.Path("checkpoints/visited_clans.json")
VISITED_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_visited_clans() -> Set[str]:
    """
    Load the set of already expanded clan tags from the checkpoint file.

    Returns
    -------
    set[str]
        A set of clan tags that have been expanded already.
        Returns an empty set if the checkpoint does not exist
        or could not be read.
    """
    if not VISITED_PATH.exists():
        return set()
    try:
        data = json.loads(VISITED_PATH.read_text())
        return set(data)
    except Exception as e:
        logger.warning("Could not load visited_clans: %s — starting with empty set", e)
        return set()


def save_visited_clans(visited: Set[str]) -> None:
    """
    Persist the set of expanded clan tags to the checkpoint file.

    Parameters
    ----------
    visited : set[str]
        The set of clan tags to persist.
    """
    VISITED_PATH.write_text(json.dumps(sorted(visited)))
    logger.info("Visited-clans checkpoint updated (%d entries)", len(visited))


def save_parquet(df: pd.DataFrame, path: str) -> None:
    """
    Save a DataFrame as a Parquet file, creating parent folders if needed.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to persist.
    path : str
        Destination path (e.g., 'data/clash_battles.parquet').
    """
    path_obj = pathlib.Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)  # ensure folder exists
    df.to_parquet(path_obj, index=False)
    logger.info("Parquet file written: %s", path_obj)


def safe_request(url: str, headers: Dict[str, str]) -> Optional[requests.Response]:
    """
    Perform a GET request with simple retry and basic rate-limit handling (HTTP 429).

    Parameters
    ----------
    url : str
        Request URL.
    headers : dict
        Request headers (must include Authorization).

    Returns
    -------
    requests.Response | None
        The successful response object, or None if all retries failed.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                logger.warning("Rate limit hit — waiting 10 seconds...")
                time.sleep(10)
            else:
                logger.warning("Unexpected status code: %s", response.status_code)
                return None
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            time.sleep(5)  # wait and retry
    return None  # after max retries give up


def parse_battle(battle: Dict) -> Optional[Dict]:
    """
    Parse a single battle JSON object into a flat dictionary of fields.

    Parameters
    ----------
    battle : dict
        Raw battle JSON as returned by the Clash Royale API.

    Returns
    -------
    dict | None
        Parsed battle record or None if parsing fails.
    """
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
            "opponent_clan": opponent.get("clan", {}).get("tag", None).replace("#", "")
                             if opponent.get("clan") else None,
            "opponent_crowns": opponent_crowns,
            "opponent_trophies": opponent_trophies,
            "opponent_deck": opponent_deck,
            "result": result,
        }
    except Exception as e:
        logger.error("Error parsing battle: %s", e)
        return None


def get_clan_members(clan_tag: str) -> List[str]:
    """
    Retrieve all member player tags for a given clan.

    Parameters
    ----------
    clan_tag : str
        Clan tag without the leading '#'.

    Returns
    -------
    list[str]
        List of player tags (without '#'). Returns an empty list on error.
    """
    url = f"{BASE_URL}/clans/%23{clan_tag}/members"
    response = safe_request(url, headers=HEADERS)
    if response is None:
        logger.warning("No response for clan %s", clan_tag)
        return []
    try:
        members = response.json()["items"]
        player_tags = [member["tag"][1:] for member in members]  # strip leading '#'
        return player_tags
    except Exception as e:
        logger.error("Failed to process clan members for %s: %s", clan_tag, e)
        return []


def get_battles_for_player(player_tag: str) -> List[Dict]:
    """
    Fetch and parse Ladder battles for a given player.

    Parameters
    ----------
    player_tag : str
        Player tag without the leading '#'.

    Returns
    -------
    list[dict]
        Parsed battle rows (possibly empty on error or when no Ladder battles exist).
    """
    url = f"{BASE_URL}/players/%23{player_tag}/battlelog"
    response = safe_request(url, headers=HEADERS)

    if response is None:
        logger.warning("No response for player %s", player_tag)
        return []

    try:
        battles = response.json()
        parsed_battles: List[Dict] = []
        for battle in battles:
            if battle.get("gameMode", {}).get("name") == "Ladder":
                parsed = parse_battle(battle)
                if parsed:
                    parsed_battles.append(parsed)
        return parsed_battles
    except Exception as e:
        logger.error("Failed to process battles for player %s: %s", player_tag, e)
        return []


def build_dataset_for_clan(clan_tag: str) -> pd.DataFrame:
    """
    Build a battle dataset for all members of the given clan,
    and mirror rows to include the opponent's perspective.

    Parameters
    ----------
    clan_tag : str
        Clan tag without the leading '#'.

    Returns
    -------
    pd.DataFrame
        DataFrame of parsed (and mirrored) battle rows for the clan.
    """
    all_parsed_battles: List[Dict] = []
    player_tags = get_clan_members(clan_tag)
    logger.info("Processing %d player tags for clan %s...", len(player_tags), clan_tag)

    for tag in player_tags:
        battles = get_battles_for_player(tag)
        if battles:
            all_parsed_battles.extend(battles)

    df = pd.DataFrame(all_parsed_battles)

    # Mirror each row so the opponent's perspective is captured as a separate sample.
    new_rows: List[Dict] = []
    for _, row in df.iterrows():
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
    df = pd.concat([df, df_flipped], ignore_index=True)
    logger.info("Collected %d total battles (including mirrored rows)", len(df))
    return df


def discover_and_expand(df: pd.DataFrame,
                        max_new_clans: int,
                        visited_clans: Set[str]) -> Tuple[pd.DataFrame, Set[str]]:
    """
    Discover opponent clans from the current dataset and expand into not-yet-visited clans.

    Parameters
    ----------
    df : pd.DataFrame
        The current dataset containing (at least) an 'opponent_clan' column.
    max_new_clans : int
        Maximum number of new clans to expand in this run.
    visited_clans : set[str]
        Set of clan tags that have already been expanded in previous runs.

    Returns
    -------
    (pd.DataFrame, set[str])
        The updated dataset (original + newly scraped data) and the updated set
        of visited clans.
    """
    potential_clans = df["opponent_clan"].dropna().unique()
    new_clans = [c for c in potential_clans if c not in visited_clans][:max_new_clans]
    logger.info("New (unvisited) clans discovered: %s", new_clans)

    all_new_data: List[pd.DataFrame] = []
    for clan_tag in new_clans:
        logger.info("Fetching data for new clan: %s", clan_tag)
        new_df = build_dataset_for_clan(clan_tag)
        if new_df is not None and not new_df.empty:
            all_new_data.append(new_df)
            visited_clans.add(clan_tag)
            save_visited_clans(visited_clans)

    if all_new_data:
        df = pd.concat([df] + all_new_data, ignore_index=True)

    return df, visited_clans


def build_complete_dataset(clan_tag: str, max_new_clans: int) -> None:
    """
    Build or resume the full dataset and persist results.

    The function will:
    - Load an existing Parquet dataset if present, otherwise start fresh
      from the given clan.
    - Load the visited-clans checkpoint and expand into not-yet-visited clans
      up to `max_new_clans`.
    - Save the updated dataset and the updated visited-clans checkpoint.

    Parameters
    ----------
    clan_tag : str
        Starting clan tag (without '#') for the initial scrape if no data exists yet.
    max_new_clans : int
        Maximum number of new clans to explore in this run.
    """
    path = pathlib.Path("data/clash_battles.parquet")
    if path.exists():
        logger.info("Found existing dataset — loading %s", path)
        df = pd.read_parquet(path)
    else:
        logger.info("No existing dataset found — starting fresh")
        df = build_dataset_for_clan(clan_tag)

    visited = load_visited_clans()
    expanded_df, visited = discover_and_expand(df, max_new_clans, visited)

    logger.info("%d battles scraped in total (current run included)", len(expanded_df))
    save_parquet(expanded_df, "data/clash_battles.parquet")
    save_visited_clans(visited)
    logger.info("✅ Final dataset saved & visited clans checkpoint updated.")