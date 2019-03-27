import numpy as np
import pandas as pd
from modules import players
from modules.utils import truncated_norm_distribution

ROUND_SCORE_STD = 6.5


def simulate_round(p1_skill, p2_skill, skill_factor=3, stdev=ROUND_SCORE_STD, n=10000):
    if not isinstance(p1_skill, float):
        p1_skill = np.random.choice(p1_skill)

    if not isinstance(p2_skill, float):
        p2_skill = np.random.choice(p2_skill)

    assert p1_skill <= 1 and p1_skill >= 0
    assert p2_skill <= 1 and p2_skill >= 0

    lower, upper = 0, 5 # bounds
    mid = (lower + upper) / 2.0
    mu = mid * (p1_skill - p2_skill) * skill_factor
    sigma = stdev
    scores = stats.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma).rvs(n).round(0)

    scores[scores < mid] = scores[scores < mid] - 3
    scores[scores > mid] = scores[scores > mid] - 2

    return scores


def simulate_game(simulate_round_fn, score_to_win, *args, **kwargs):
    # Simulate rounds: [-1, 1, 3...]
    diffs = simulate_round_fn(*args, **kwargs)

    # Get scores for each player: [0, 1, 3], [1, 0, 0]
    p1_score = np.ma.masked_array(diffs, mask=diffs < 0).filled(fill_value=0)
    p2_score = np.abs(np.ma.masked_array(diffs, mask=diffs > 0)).filled(fill_value=0)

    # Aggregate cumulative score: [[0, 1, 4], [1, 1, 1]]
    score_table = np.cumsum(np.array((p1_score, p2_score)), axis=1)

    # Get the score of the leader after each round
    leading_score = np.max(score_table, axis=0)

    # Get the first round when one player reaches the score needed to win
    win_round = np.argwhere(leading_score >= score_to_win)[0][0]
    p1_score, p2_score = score_table[:, win_round]

    return p1_score, p2_score


def simulate_many_games(n_games, simulate_round_fn, score_to_win, *args, **kwargs):
    scores = map(lambda i: simulate_game(simulate_round_fn, score_to_win,
                                       *args, **kwargs), range(n_games))
    df_games = pd.DataFrame(scores)
    df_games.columns = ["p1_score", "p2_score"]
    p1_wins = df_games["p1_score"] > df_games["p2_score"]


    #df_games.loc[p1_wins, "winner"] = "p1"
    #df_games.loc[~p1_wins, "winner"] = "p2"

    meta = pd.Series()
    meta["p1_wins"] = df_games[p1_wins].shape[0]
    meta["p2_wins"] = df_games[~p1_wins].shape[0]
    meta["p1_win_prob"] = meta["p1_wins"] / float(n_games)
    meta["p2_win_prob"] = meta["p2_wins"] / float(n_games)
    diff = df_games["p1_score"] - df_games["p2_score"]
    meta["sim_mean_diff"] = diff.mean()
    meta["sim_mean_diff_abs"] = np.abs(diff.mean())
    meta["sim_most_common_diff"] = diff.mode().iloc[0]
    meta["scores"] = scores

    results = df_games["p1_score"].astype(int).astype(str) + "-" + df_games["p2_score"].astype(int).astype(str)
    meta["result_counts"] = results.value_counts()

    return meta
