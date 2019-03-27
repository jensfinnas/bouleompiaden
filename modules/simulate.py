import numpy as np
import pandas as pd
from modules import players
from modules.utils import truncated_norm_distribution
from modules.common import simulate_many_games
from modules.models import simulate_round_v4

ROUND_SCORE_STD = 6.5
SKILL_FACTOR = 12.0

def game(player1, player2, n_games=1000):
    p1 = players.get(player1)
    p2 = players.get(player2)

    MIN_STD = 0.05 # alla antas ha minst denna osäkerhet
    MAX_STD = 0.15 # högsta osäkerhet
    N_GAME_CAP = 10.0 # Har spelaren gjort så här många matcher får den max osäkerhet

    # Cap skill skill uncertainty, but avoid division by zero
    p1_n_games = max(min(p1["n_games"], N_GAME_CAP), 1)
    p2_n_games = max(min(p2["n_games"], N_GAME_CAP), 1)


    p1["skill_uncertainty"] = MIN_STD + (1 - p1_n_games / N_GAME_CAP)  * (MAX_STD - MIN_STD)
    p2["skill_uncertainty"] = MIN_STD + (1 - p2_n_games / N_GAME_CAP) * (MAX_STD - MIN_STD)

    p1_skill_dist = truncated_norm_distribution(p1["skill"], p1["skill_uncertainty"], 0, 1, 1000)
    p2_skill_dist = truncated_norm_distribution(p2["skill"], p2["skill_uncertainty"], 0, 1, 1000)


    resp = simulate_many_games(n_games, simulate_round_v4, 8, p1_skill_dist, p2_skill_dist, skill_factor=SKILL_FACTOR, stdev=ROUND_SCORE_STD)
    resp["p1"] = p1
    resp["p2"] = p2

    return resp
