import json
from trueskill import  Rating
from slugify import slugify
import os

from settings import BY_PLAYER_FILE, META_DATA_FILE, GAMES_BY_PLAYER_FILE, TRUE_SKILL_BASE


with open(META_DATA_FILE) as f:
    metadata = json.load(f)

def all():
    with open(BY_PLAYER_FILE) as f:
        players = json.load(f)

    """Get a list of all players."""
    return players.values()

def get(player_name=None, player_slug=None):
    if player_slug is None:
        player_slug = slugify(player_name)
    file_path = os.path.join("data", "players", player_slug + ".json")
    with open(file_path) as f:
        player = json.load(f)

    player["rating"] = Rating(mu=player["skill"],
                                sigma=player["skill_sigma"])
    return player
    """

    try:
        player = players[player_name]
        player["rating"] = Rating(mu=player["skill"],
                                  sigma=player["skill_sigma"])
    except KeyError:
        # New/unrecognized player
        player = {
            "n_games": 0,
            "opponent_score_share": 0.5,
            "skill": TRUE_SKILL_BASE,
            "rating": Rating(),
            "n_wins": 0,
            "win_rate": 0,
            "score_share": 0,
            "skill_rank": None,
            "skill_rank_pct": None,
            "years": []
        }        
    return player
    """

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
