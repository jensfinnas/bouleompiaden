import pandas as pd
import json
from ast import literal_eval

from settings import PLAYER_DATA_FILE, GAMES_BY_PLAYER_FILE

def all():
    """Get a list of all players."""
    return pd.read_csv(PLAYER_DATA_FILE, encoding="utf-8")["name"].tolist()

def get(player_name):
    df_players = pd.read_csv(PLAYER_DATA_FILE, encoding="utf-8").set_index("name")

    try:
        player = df_players.loc[player_name]
        player["years"] = literal_eval(player["years"])
    except KeyError:
        # New/unrecognized player
        player = pd.Series({
            "n_games": 0,
            "opponent_score_share": 0.5,
            "skill": 0.5,
            "n_wins": 0,
            "win_rate": 0,
            "score_share": 0,
            "years": []
        }, name=player_name)
    return player.to_dict()

def previous_mutual_games(player1, player2):
    """Get all historical games between two players.
    """
    games = []
    with open(GAMES_BY_PLAYER_FILE) as f:
        games_by_player = json.load(f)

    try:
        for game in games_by_player[player1]:
            if game["opponent"] == player2:
                games.append({
                    "year": game["year"],
                    "p1_score": game["player_score"],
                    "p2_score": game["opponent_score"],
                    "winner": game["winner"],
                })
    except KeyError:
        # don't crash if a plarye
        games = []

    return games
