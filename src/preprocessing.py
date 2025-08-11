import ast
import pandas as pd

def preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert string representations of decks into Python lists.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing the columns 'player_deck' and 'opponent_deck'.

    Returns
    -------
    pd.DataFrame
        Modified DataFrame where both deck columns contain Python lists 
        instead of strings.
    """
    df["player_deck"] = df["player_deck"].apply(ast.literal_eval)
    df["opponent_deck"] = df["opponent_deck"].apply(ast.literal_eval)
    return df