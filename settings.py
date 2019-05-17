import os

"""Input data"""
PLAYER_DATA_FILE = "data/by_player.csv"
GAMES_BY_PLAYER_FILE = "data/games_by_player.json"

STAGE = os.environ.get("STAGE", "local")
