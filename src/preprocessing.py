import ast
import pandas as pd

def preprocessing(df):
    df["player_deck"] = df["player_deck"].apply(ast.literal_eval)
    df["opponent_deck"] = df["opponent_deck"].apply(ast.literal_eval)
    return df