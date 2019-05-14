import pandas as pd
import json

from settings import PLAYER_DATA_FILE

def all():
    """Get a list of all players."""
    return pd.read_csv(PLAYER_DATA_FILE, encoding="utf-8")["name"].tolist()

def get(player_name):
    df_players = pd.read_csv(PLAYER_DATA_FILE, encoding="utf-8").set_index("name")

    try:
        player = df_players.loc[player_name]
    except KeyError:
        player = pd.Series({
            "n_games": 0,
            "opponent_score_share": 0.5,
            "skill": 0.5,
        }, name=player_name)
    return player.to_dict()
