import os
from trueskill import TrueSkill
"""Input data"""
PLAYER_DATA_FILE = "data/by_player.csv"
GAMES_BY_PLAYER_FILE = "data/games_by_player.json"
BY_PLAYER_FILE = "data/by_player.json"
META_DATA_FILE = "data/metadata.json"

STAGE = os.environ.get("STAGE", "local")


#
TRUE_SKILL_BASE = 100.0 # base rating/skill
TRUE_SKILL_SIGMA = TRUE_SKILL_BASE / 1.0 # the initial standard deviation of ratings. The recommended value is a third of mu.
TRUE_SKILL_BETA = TRUE_SKILL_SIGMA * 1.0 # the distance which guarantees about 76% chance of winning. The recommended value is a half of sigma.

true_skill_env = TrueSkill(draw_probability=0, mu=TRUE_SKILL_BASE,
                           sigma=TRUE_SKILL_SIGMA, beta=TRUE_SKILL_BETA)
true_skill_env.make_as_global()
