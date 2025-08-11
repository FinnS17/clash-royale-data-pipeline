import requests
from api_config import HEADERS
from api_config import BASE_URL
import pandas as pd
import numpy as np

import logging
logger = logging.getLogger(__name__)

def get_all_cards():
    """
    Fetches all available card names from the Clash Royale API.

    Returns:
        list[str]: A list of card names if the request is successful.
                   Returns None and logs an error if the request fails.
    """
    url = f"{BASE_URL}/cards"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        cards = response.json()["items"]
        return [card["name"] for card in cards]
    else: 
        logger.error("Error fetching cards: %d", response.status_code)


def one_hot_encode_cards(df, all_cards):
    """
    Adds one-hot encoded columns for each card to the given DataFrame.

    Each card gets a column with 1 if the card is present in the player's deck, 
    otherwise 0.

    Note:
        This step is NOT mandatory for building the dataset itself.
        However, it is recommended for downstream analysis or machine learning 
        tasks that require numerical features.

    Args:
        df (pd.DataFrame): DataFrame containing at least a 'player_deck' column 
                           with lists of card names.
        all_cards (list[str]): List of all possible card names.

    Returns:
        pd.DataFrame: Original DataFrame with additional one-hot encoded columns.
    """
    card_dfs = []
    for card in all_cards:
        card_series = df["player_deck"].apply(lambda x: 1 if card in x else 0)
        card_dfs.append(card_series.rename(card))

    one_hot_df = pd.concat(card_dfs, axis=1)
    return pd.concat([df, one_hot_df], axis=1)


def bin_trophie_column(df):
    """
    Categorizes player trophies into discrete ranges and adds one-hot encoded columns.

    Trophy ranges:
        - "low": less than 4000
        - "mid": 4000 to less than 6000
        - "high": 6000 or more

    Note:
        This step is NOT mandatory for building the dataset itself.
        However, it is useful for later analysis or modeling to group players 
        into skill/trophy segments.

    Args:
        df (pd.DataFrame): DataFrame containing a 'player_trophies' column.

    Returns:
        pd.DataFrame: DataFrame with a 'trophie_range' column (one-hot encoded).
    """
    def trophy_bin(t):
        if t < 4000:
            return "low"
        elif t < 6000:
            return "mid"
        else:
            return "high" 

    df["trophie_range"] = df["player_trophies"].apply(trophy_bin)
    df = pd.get_dummies(df, columns=["trophie_range"])
    return df