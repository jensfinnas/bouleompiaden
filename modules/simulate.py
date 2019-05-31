import numpy as np
import pandas as pd
import math
from modules import players
from modules.utils import truncated_norm_distribution
from modules.common import simulate_many_games
from settings import true_skill_env



def game(player1, player2):
    """Simulate a game between two players.

    :param player1: name of player1
    :param player2: name of player2
    """
    p1 = players.get(player1)
    p2 = players.get(player2)

    resp = {
        "p1": p1,
        "p2": p2,
    }
    resp["p1_win_prob"] = _win_probability([p1["rating"]], [p2["rating"]])
    resp["p2_win_prob"] = 1 - resp["p1_win_prob"]

    return resp


def _win_probability(a, b):
    """Calcaluates the probaility of a beating b.

    Copy-paste from:
    https://github.com/sublee/trueskill/issues/1#issuecomment-149762508
    """
    deltaMu = sum([x.mu for x in a]) - sum([x.mu for x in b])
    sumSigma = sum([x.sigma ** 2 for x in a]) + sum([x.sigma ** 2 for x in b])
    playerCount = len(a) + len(b)
    beta = true_skill_env.beta
    denominator = math.sqrt(playerCount * (beta * beta) + sumSigma)
    return true_skill_env.cdf(deltaMu / denominator)
