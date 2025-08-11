from preprocessing import preprocessing
import pandas as pd
from feature_engineering import get_all_cards, one_hot_encode_cards, bin_trophie_column
import requests
from api_config import HEADERS, BASE_URL


df = pd.read_csv("data/clash_battles3.csv")
df = preprocessing(df)
all_cards = get_all_cards()
df = one_hot_encode_cards(df, all_cards)
df = bin_trophie_column(df)



