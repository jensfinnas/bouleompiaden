"""Takes
"""
import pandas as pd
import numpy as np
import os
import json
from copy import deepcopy
from pandas.api.types import is_bool_dtype
from slugify import slugify
from collections import  defaultdict
from trueskill import TrueSkill, Rating, rate_1vs1
from modules.simulate import get_win_probability

from settings import (BY_PLAYER_FILE, GAMES_BY_PLAYER_FILE, META_DATA_FILE,
                      MARATHON_FILE, MARATHON_SCORE_PER_STAGE,
                      TRUE_SKILL_BASE, TRUE_SKILL_BETA, TRUE_SKILL_SIGMA)

STAGES = [
    "gruppspel",
    "sextondelsfinal",
    "åttondelsfinal",
    "kvartsfinal",
    "semifinal",
    "bronsmatch",
    "brons",
    "final",
    "vinnare",
]

###
# Prepare raw data
###
df = pd.read_csv("data/input/Bouleompiaden _ Statistikdatabasen - Data_ Matcher.csv", encoding="utf-8")\
.rename(columns={
    u"Spelare 1": "p1_name",
    u"Spelare 2": "p2_name",
    u"Poäng 1": "p1_score",
    u"Poäng 2": "p2_score",
    "Turnering": "year",
    u"Nivå": "stage"})\
[["year", "p1_name", "p2_name","p1_score", "p2_score", "stage"]]

df["stage"] = df["stage"].str.lower()
df["stage_level"] = df["stage"].apply(STAGES.index)
assert df["stage"].isin(STAGES).all()
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
df.loc[p1_won, "loser_name"] = df.loc[p1_won, "p2_name"]
df.loc[~p1_won, "loser_name"] = df.loc[~p1_won, "p1_name"]

df["winner_points"] = df[["p1_score", "p2_score"]].max(axis=1)

is_medal_game = df["stage"].isin(["bronsmatch", "final"])
df.loc[is_medal_game, "score_to_win"] = 12

df.loc[is_medal_game, "score_to_win"] = 12
df.loc[~is_medal_game, "score_to_win"] = 8

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
        p1_skill = player_skills[p1][-1][1]
    except (KeyError, IndexError):
        p1_skill = Rating()

    try:
        p2_skill = player_skills[p2][-1][1]
    except (KeyError, IndexError):
        p2_skill = Rating()
    
    p1_win_prob = get_win_probability([p1_skill], [p2_skill])
    p2_win_prob = 1 - p1_win_prob
    df.loc[ix, "p1_win_prob"] = p1_win_prob
    df.loc[ix, "p2_win_prob"] = p2_win_prob
    df.loc[ix, "winner_win_prob"] =  p1_win_prob if game["winner"] == "p1" else p2_win_prob

    if game[u"p1_score"] > game[u"p2_score"]:
        p1_new_skill, p2_new_skill = rate_1vs1(p1_skill, p2_skill)
    else:
        p2_new_skill, p1_new_skill = rate_1vs1(p2_skill, p1_skill)

    player_skills[p1].append((game["year"], p1_new_skill))
    player_skills[p2].append((game["year"], p2_new_skill))

###
# Prepare by player data
###
base_cols = ["game_id", "year", "stage", "stage_level", "winner"]
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
is_final_winner = (df_long["stage"]=="final") & df_long["is_winner"]
df_long.loc[is_final_winner, "stage"] = "vinnare"
df_long.loc[is_final_winner, "stage_level"] = STAGES.index("vinnare")
is_bronze_winner = (df_long["stage"]=="bronsmatch") & df_long["is_winner"]
df_long.loc[is_bronze_winner, "stage"] = "brons"
df_long.loc[is_bronze_winner, "stage_level"] = STAGES.index("brons")

df_long["opponent_slug"] = df_long["opponent_name"].apply(slugify)


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



for player, skill_history in player_skills.items():
    df_players.loc[player, "skill"] = skill_history[-1][1].mu
    df_players.loc[player, "skill_sigma"] = skill_history[-1][1].sigma
    # {2017: 123, 2018: 132}
    player_skills[player] = dict([(year, np.round(skill.mu)) 
                                   for i, (year, skill) in enumerate(skill_history) 
                                   if (i == len(skill_history) - 1) or skill_history[i+1][0] != year])


    #df_players.loc[player, "skill_history"] = ",".join([str(x.mu) for x in skill_history])

df_players["name"] = df_players.index
df_players["slug"] = df_players["name"].apply(slugify)
df_players["skill_rank"] = df_players["skill"].rank(ascending=False)
df_players["skill_rank_pct"] = df_players["skill"].rank(ascending=False)


players_json = df_players.to_dict("index")

years = df["year"].sort_values().unique()
for player, player_json in players_json.items():
    # get skill history
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

    # Generera data om alla turneringar spelaren varit med i
    df_player_games = df_long[df_long["name"] == player]
    player_json["tournaments"] = []
    for year, df_player_year_games in df_player_games.sort_values(["year", "stage_level"]).groupby("year"):
        cols = ["opponent_name", "opponent_slug", "score", "opponent_score", "is_winner", "stage"]
        tournament_json = {
            "year": year,
            "last_game": df_player_year_games.iloc[-1][cols].to_dict(),
            "games": df_player_year_games.to_dict("records"),
            "n_games": df_player_year_games.shape[0],
            "n_wins": df_player_year_games["is_winner"].sum(),
        }
        player_json["tournaments"].append(tournament_json)

    # bästa resultat
    best_stage = df_player_games["stage_level"].max()
    player_json["best_stage"] = STAGES[best_stage]
    player_json["best_stage_years"] = df_player_games[df_player_games["stage_level"]==best_stage]["year"].unique().tolist()

def default(o):
    """serialize"""
    if isinstance(o, np.int64): 
        return int(o)
    elif is_bool_dtype(o):
        return bool(o)
    raise TypeError

for player, player_json in players_json.items():
    file_name = player_json['slug'] + ".json"
    file_path = os.path.join("data", "players", file_name)
    with open(file_path, 'w') as f:
        json.dump(player_json, f, indent=2, default=default)
        print(f"Updated {file_path}")

players_json_slim = deepcopy(players_json)
for player, player_json in players_json_slim.items():
    del player_json["tournaments"]

with open(BY_PLAYER_FILE, 'w') as f:
    json.dump(players_json_slim, f, indent=2, default=default)
print("Updated {}".format(BY_PLAYER_FILE))

###
# Prepare marathon table
### 

def get_marathon_score(df_player):
    df_last_games = df_player.groupby("year")["stage"].last().to_frame()
    df_last_games["stage_score"] = df_last_games["stage"]\
                    .apply(MARATHON_SCORE_PER_STAGE.get)\
                    .fillna(0)
    resp = df_last_games.groupby("stage").count()
    resp.loc["marathon_score"] = df_last_games["stage_score"].sum()
    return resp.T.loc["stage_score"]

df_marathon = df_long.sort_values(["name", "year", "stage_level"])\
                     .groupby("name").apply(get_marathon_score)\
                     .unstack()\
                     .fillna(0)\
                     .sort_values("marathon_score", ascending=False)\
                     [STAGES + ["marathon_score"]]

df_marathon["marathon_rank"] = df_marathon["marathon_score"].rank(ascending=False, method="min")

export_cols = list(MARATHON_SCORE_PER_STAGE.keys()) + ["marathon_score", "marathon_rank"]
marathon_json = df_marathon[export_cols]\
                .query("marathon_score > 0")\
                .reset_index()\
                .to_dict("records")

with open(MARATHON_FILE, 'w') as f:
    json.dump(marathon_json, f, indent=2)
print("Updated {}".format(MARATHON_FILE))


###
# Prepare game data
###
games_json = {}
for player in df_players.index.unique():
    p1_games = (df[df["p1_name"] == player]
                [["year", "p2_name", "p1_score", "p2_score", "winner_name"]]
                .rename(columns={"p1_score": "player_score",
                                 "p1_win_prob": "win_prob",
                                 "p2_score": "opponent_score",
                                 "p2_name": "opponent",
                                 "p2_win_prob": "opponent_win_prob",
                                 "winner_name": "winner"})
                )
    p2_games = (df[df["p2_name"] == player]
                [["year", "p1_name", "p1_score", "p2_score", "winner_name"]]
                .rename(columns={"p2_score": "player_score",
                                 "p2_win_prob": "win_prob",
                                 "p1_score": "opponent_score",
                                 "p1_name": "opponent",
                                 "p1_win_prob": "opponent_win_prob",
                                 "winner_name": "winner"})
                )
    df_games = pd.concat([p1_games, p2_games], sort=False)
    df_games["is_winner"] = df_games["winner"] == player
    games_json[player] = df_games.to_dict("records")


with open(GAMES_BY_PLAYER_FILE, 'w') as f:
    json.dump(games_json, f, indent=2)
print("Updated {}".format(GAMES_BY_PLAYER_FILE))

###
# Prepare tournament data
###

def get_performance(x):
    """Performance är ett mått hur bra varje spelare presterat år för år i förhållande till
    sina odds.  
    """
    return ((x[x.is_winner]["opponent_win_prob"].sum() - # 1. motståndrens vinstchans i vinstmatcher
             x[~x.is_winner]["win_prob"].sum()) / # 2. minus egen vinstchans i förlustmatcher
            len(x.index) # 3. dividerat med antal matcher
            )
s_performance = df_long.groupby(["year", "name"]).apply(get_performance).rename("performance")

for year, df_year in df.groupby("year"):
    tournament = {
        "year": year,
        "playoff": [],
    }
    s_final = df_year.set_index("stage").loc["final"]
    tournament["gold"] = s_final["winner_name"]
    tournament["silver"] = s_final["loser_name"]
    if "bronsmatch" in df_year["stage"].unique():
        s_bronsmatch = df_year.set_index("stage").loc["bronsmatch"]
        tournament["bronze"] = s_bronsmatch["winner_name"]

    # lista slutspelts
    for stage in STAGES:
        if stage in df_year["stage"].unique() and stage != "gruppspel":
            df_stage_games = df_year[df_year["stage"]==stage]
            cols = ["p1_name","p2_name","p1_score", "p2_score","winner"]
            tournament["playoff"].append({
                "stage": stage,
                "games": df_stage_games[cols].to_dict("records"),
            })
    tournament["top_performers"] = s_performance[s_performance > 0].loc[year]\
                                                .sort_values(ascending=False)\
                                                .head(15)\
                                                .reset_index()\
                                                .to_dict("records")

    df_tourn_games = df[df["year"] == year]
    tournament["top_low_prob_winners"] = df_tourn_games.sort_values("winner_win_prob")\
                                            [["winner_name", "loser_name", "winner_win_prob", "stage"]]\
                                            .head(10)\
                                            .to_dict("records")
    

    # save
    file_path = os.path.join("data", "tournaments", f"{year}.json")
    with open(file_path, 'w') as f:
        json.dump(tournament, f, indent=2, default=default)
        print(f"Updated {file_path}")


###
# Prepare meta data
###
metadata = {
    "n_players": len(df_players.index),
    "years": df["year"].sort_values().unique().tolist(),
    "highest_skill": df_players["skill"].max(),
    "lowest_skill": df_players["skill"].min(),
    "marathon_score_per_stage": MARATHON_SCORE_PER_STAGE,
}
with open(META_DATA_FILE, 'w') as f:
    json.dump(metadata, f, indent=2)
print("Updated {}".format(META_DATA_FILE))

###
# store csv files
###
OUTPUT_DIR = "data/generated-tables"

# by player
file_path = os.path.join(OUTPUT_DIR, "players.csv")
df_players.to_csv(file_path)
print(f"Update {file_path}")

# by game
file_path = os.path.join(OUTPUT_DIR, "games.csv")
df_games.to_csv(file_path)
print(f"Update {file_path}")

# marathon table
file_path = os.path.join(OUTPUT_DIR, "marathon_table.csv")
df_marathon.to_csv(file_path)
print(f"Update {file_path}")