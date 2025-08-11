import requests
from api_config import HEADERS
from api_config import BASE_URL
import pandas as pd
from gensim.models import Word2Vec
import numpy as np

def get_all_cards():
    url = f"{BASE_URL}/cards"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        cards = response.json()["items"]
        return [card["name"] for card in cards]
    else: 
        print(f"Error: {response.status_code}")


def one_hot_encode_cards(df, all_cards):
    """Fügt dem DataFrame für jede Karte eine Spalte hinzu mit 1/0, je nachdem ob die Karte im Deck ist."""
    card_dfs = []

    for card in all_cards:
        card_series = df["player_deck"].apply(lambda x: 1 if card in x else 0)
        card_dfs.append(card_series.rename(card))

    one_hot_df = pd.concat(card_dfs, axis=1)
    return pd.concat([df, one_hot_df], axis=1)

def bin_trophie_column(df):
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

