import numpy as np
from modules.utils import truncated_norm_distribution

def simulate_round_v4(p1_skill, p2_skill, skill_factor=3, stdev=6.5, n=10000):
    if not isinstance(p1_skill, float):
        p1_skill = np.random.choice(p1_skill)

    if not isinstance(p2_skill, float):
        p2_skill = np.random.choice(p2_skill)

    assert p1_skill <= 1 and p1_skill >= 0
    assert p2_skill <= 1 and p2_skill >= 0

    lower, upper = 0, 5 # bounds
    mid = (lower + upper) / 2.0
    mu = mid + mid * (p1_skill - p2_skill) * skill_factor
    sigma = stdev

    scores = truncated_norm_distribution(mu, sigma, lower, upper, n).round(0)

    scores[scores < mid] = scores[scores < mid] - 3
    scores[scores > mid] = scores[scores > mid] - 2

    return scores
