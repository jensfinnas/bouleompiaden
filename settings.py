import os
from trueskill import TrueSkill
"""Input data"""
PLAYER_DATA_FILE = "data/by_player.csv"
GAMES_BY_PLAYER_FILE = "data/games_by_player.json"
BY_PLAYER_FILE = "data/by_player.json"
META_DATA_FILE = "data/metadata.json"
PLAYER_DATA_DIR = "data/players"

STAGE = os.environ.get("STAGE", "local")

# the ranking that new players start from
TRUE_SKILL_BASE = 100.0

# the initial standard deviation of ratings. The recommended value is a third of mu.
# but we keep it sligtly higher as there seem to be quite a bit of uncertainty
# about the skill level of players (source: mostly gut feeling)
TRUE_SKILL_SIGMA = TRUE_SKILL_BASE / 1.0
TRUE_SKILL_BETA = TRUE_SKILL_SIGMA * 0.5 # the distance which guarantees about 76% chance of winning. The recommended value is a half of sigma.

true_skill_env = TrueSkill(draw_probability=0, mu=TRUE_SKILL_BASE,
                           sigma=TRUE_SKILL_SIGMA, beta=TRUE_SKILL_BETA)
true_skill_env.make_as_global()
