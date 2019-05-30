import numpy as np
import pandas as pd
import math
from modules import players
from modules.utils import truncated_norm_distribution
from modules.common import simulate_many_games
from settings import true_skill_env


def win_probability(a, b):
    deltaMu = sum([x.mu for x in a]) - sum([x.mu for x in b])
    sumSigma = sum([x.sigma ** 2 for x in a]) + sum([x.sigma ** 2 for x in b])
    playerCount = len(a) + len(b)
    beta = true_skill_env.beta
    denominator = math.sqrt(playerCount * (beta * beta) + sumSigma)
    return true_skill_env.cdf(deltaMu / denominator)

def game(player1, player2, n_games=1000):
    p1 = players.get(player1)
    p2 = players.get(player2)

    resp = {
        "p1": p1,
        "p2": p2,
    }
    resp["p1_win_prob"] = win_probability([p1["rating"]], [p2["rating"]])
    resp["p2_win_prob"] = 1 - resp["p1_win_prob"]

    return resp
