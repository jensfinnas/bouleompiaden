"""Takes
"""
import pandas as pd
import numpy as np
import json
from collections import  defaultdict
from trueskill import TrueSkill, Rating, rate_1vs1
from settings import BY_PLAYER_FILE, GAMES_BY_PLAYER_FILE, META_DATA_FILE, TRUE_SKILL_BASE, TRUE_SKILL_BETA, TRUE_SKILL_SIGMA


###
# Prepare raw data
###
df = pd.read_csv("data/Bouleompiaden _ Statistikdatabasen - Data_ Matcher.csv", encoding="utf-8")\
.rename(columns={
    u"Spelare 1": "p1_name",
    u"Spelare 2": "p2_name",
    u"Poäng 1": "p1_score",
    u"Poäng 2": "p2_score",
    "Turnering": "year",
    u"Nivå": "stage"})\
[["year", "p1_name", "p2_name","p1_score", "p2_score", "stage"]]

df["game_id"] = df.index
total_score = df[["p1_score", "p2_score"]].sum(axis=1)
df["diff"] = df["p1_score"] - df["p2_score"]
df["p1_score_share"] = df["p1_score"] / total_score
df["p2_score_share"] = df["p2_score"] / total_score

p1_won = df["p1_score"] > df["p2_score"]
df.loc[p1_won, "winner"] = "p1"
df.loc[~p1_won, "winner"] = "p2"
df.loc[p1_won, "winner_name"] = df.loc[p1_won, "p1_name"]
df.loc[~p1_won, "winner_name"] = df.loc[~p1_won, "p2_name"]

df["winner_points"] = df[["p1_score", "p2_score"]].max(axis=1)

is_medal_game = df["stage"].isin(["Bronsmatch", "Final"])
df.loc[is_medal_game, "score_to_win"] = 12

df.loc[is_medal_game, "score_to_win"] = 12
df.loc[~is_medal_game, "score_to_win"] = 8

###
# Prepare by player data
###
base_cols = ["game_id", "year", "stage", "winner"]
p1_cols = [x for x in df.columns if x.startswith("p1")]
p2_cols = [x for x in df.columns if x.startswith("p2")]
new_col_names = [x.split("_", 1)[1] for x in p1_cols]
opponent_col_names = [u"opponent_" + x for x in new_col_names]

p1_col_translation = dict(zip(p1_cols + p2_cols, new_col_names + opponent_col_names))
p2_col_translation = dict(zip(p2_cols + p1_cols, new_col_names + opponent_col_names))

df_p1 = df[base_cols + p1_cols + p2_cols].rename(columns=p1_col_translation)
df_p2 = df[base_cols + p1_cols + p2_cols].rename(columns=p2_col_translation)

df_long = pd.concat([df_p1, df_p2], sort=False, axis=0)
df_long["is_winner"] = df_long["score"] > df_long["opponent_score"]

by_player = df_long.groupby("name")
df_players = pd.concat([
    by_player["name"].count().rename("n_games"),
    by_player["score_share"].mean(),
    by_player["is_winner"].sum().rename("n_wins"),
    by_player["year"].apply(lambda x: list(np.sort(x.unique()))).rename("years"),
], axis=1)
df_players["win_rate"] = df_players["n_wins"] / df_players["n_games"]

# Add component score share
df_long = df_long.merge(df_players["score_share"].rename("opponent_hist_score_share").to_frame(), left_on="opponent_name", right_index=True)
df_players["opponent_score_share"] = df_long.groupby("name")["opponent_hist_score_share"].mean()
df_players.sort_values("opponent_score_share")

# Compute skill
true_skill_env = TrueSkill(draw_probability=0, mu=TRUE_SKILL_BASE,
                           sigma=TRUE_SKILL_SIGMA, beta=TRUE_SKILL_BETA)
true_skill_env.make_as_global()

player_skills = defaultdict(list)

for ix, game in df.iterrows():
    p1 = game["p1_name"]
    p2 = game["p2_name"]

    try:
        p1_skill = player_skills[p1][-1][1]
    except (KeyError, IndexError):
        p1_skill = Rating()

    try:
        p2_skill = player_skills[p2][-1][1]
    except (KeyError, IndexError):
        p2_skill = Rating()

    if game[u"p1_score"] > game[u"p2_score"]:
        p1_new_skill, p2_new_skill = rate_1vs1(p1_skill, p2_skill)
    else:
        p2_new_skill, p1_new_skill = rate_1vs1(p2_skill, p1_skill)

    player_skills[p1].append((game["year"], p1_new_skill))
    player_skills[p2].append((game["year"], p2_new_skill))

for player, skill_history in player_skills.items():
    df_players.loc[player, "skill"] = skill_history[-1][1].mu
    df_players.loc[player, "skill_sigma"] = skill_history[-1][1].sigma
    # {2017: 123, 2018: 132}
    player_skills[player] = dict([(year, np.round(skill.mu)) for i, (year, skill) in enumerate(skill_history) if (i == len(skill_history) - 1) or skill_history[i+1][0] != year])


    #df_players.loc[player, "skill_history"] = ",".join([str(x.mu) for x in skill_history])

df_players["name"] = df_players.index
df_players["skill_rank"] = df_players["skill"].rank(ascending=False)
df_players["skill_rank_pct"] = df_players["skill"].rank(ascending=False)

players_json = df_players.to_dict("index")

years = df["year"].sort_values().unique()
for player, player_json in players_json.items():
    skill_history = player_skills[player]
    players_json[player]["skill_history"] = []
    prev_skill = None
    for year in years:
        if year in skill_history:
            skill = skill_history[year]
        else:
            skill = None
        prev_skill = skill
        players_json[player]["skill_history"].append((year, skill))

def default(o):
    """serialize numpy.int64"""
    if isinstance(o, np.int64): return int(o)
    raise TypeError

with open(BY_PLAYER_FILE, 'w') as f:
    json.dump(players_json, f, indent=2, default=default)
print("Updated {}".format(BY_PLAYER_FILE))


###
# Prepare game data
###
games_json = {}
for player in df_players.index.unique():
    p1_games = (df[df["p1_name"] == player]
                [["year", "p2_name", "p1_score", "p2_score", "winner_name"]]
                .rename(columns={"p1_score": "player_score",
                                 "p2_score": "opponent_score",
                                 "p2_name": "opponent",
                                 "winner_name": "winner"})
                )
    p2_games = (df[df["p2_name"] == player]
                [["year", "p1_name", "p1_score", "p2_score", "winner_name"]]
                .rename(columns={"p2_score": "player_score",
                                 "p1_score": "opponent_score",
                                 "p1_name": "opponent",
                                 "winner_name": "winner"})
                )
    df_games = pd.concat([p1_games, p2_games], sort=False)
    df_games["is_winner"] = df_games["winner"] == player
    games_json[player] = df_games.to_dict("records")


with open(GAMES_BY_PLAYER_FILE, 'w') as f:
    json.dump(games_json, f, indent=2)
print("Updated {}".format(GAMES_BY_PLAYER_FILE))

###
# Prepare meta data
###
metadata = {
    "n_players": len(df_players.index),
    "years": df["year"].sort_values().unique().tolist(),
    "highest_skill": df_players["skill"].max(),
    "lowest_skill": df_players["skill"].min()
}
with open(META_DATA_FILE, 'w') as f:
    json.dump(metadata, f, indent=2)
print("Updated {}".format(META_DATA_FILE))
