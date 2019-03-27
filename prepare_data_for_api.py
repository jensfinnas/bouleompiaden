"""Takes
"""
import pandas as pd
import json
from settings import PLAYER_DATA_FILE

OUTFILE = PLAYER_DATA_FILE

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
], axis=1)
df_players["win_rate"] = df_players["n_wins"] / df_players["n_games"]

# Add component score share
df_long = df_long.merge(df_players["score_share"].rename("opponent_hist_score_share").to_frame(), left_on="opponent_name", right_index=True)
df_players["opponent_score_share"] = df_long.groupby("name")["opponent_hist_score_share"].mean()
df_players.sort_values("opponent_score_share")

best_score_share = df_players["score_share"].max()


df_players["opponent_skill"] = df_players["opponent_score_share"] / best_score_share
df_players["skill"] = df_players["score_share"] /  best_score_share * (df_players["opponent_skill"] / 0.5)

best_skill = df_players["skill"].max()
df_players["skill"] = df_players["skill"] / best_skill

df_players.to_csv(OUTFILE, encoding="utf-8")
print("Updated {}".format(OUTFILE))

"""
###
# Compute skill
###

ss = df_players["score_share"]
df = df.merge(ss.rename("p1_hist_score_share").to_frame(), how="left", left_on="p1_name", right_index=True)
df = df.merge(ss.rename("p2_hist_score_share").to_frame(), how="left", left_on="p2_name", right_index=True)

oss = df_players["opponent_score_share"]
df = df.merge(oss.rename("p1_opponent_hist_score_share").to_frame(), how="left", left_on="p1_name", right_index=True)
df = df.merge(oss.rename("p2_opponent_hist_score_share").to_frame(), how="left", left_on="p2_name", right_index=True)

best_score_share =  df_players["score_share"].max()

df["p1_opponent_skill"] = df["p1_opponent_hist_score_share"] /  best_score_share
df["p2_opponent_skill"] = df["p2_opponent_hist_score_share"] / best_score_share


df["p1_skill"] = df["p1_hist_score_share"] /  best_score_share * (df["p1_opponent_skill"] / 0.5)
df["p2_skill"] = df["p2_hist_score_share"] / best_score_share * (df["p2_opponent_skill"] / 0.5)

best_skill = df[["p1_skill","p2_skill"]].max().max()

df["p1_skill"] = df["p1_skill"] / best_skill
df["p2_skill"] = df["p2_skill"] / best_skill

df.loc[df["p1_skill"].isna(), "p1_skill"] = 0.5
df.loc[df["p2_skill"].isna(), "p2_skill"] = 0.5

import pdb; pdb.set_trace()

n_games = df_players["n_games"]
df = df.merge(n_games.rename("p1_n_games").to_frame(), how="left", left_on="p1_name", right_index=True)
df = df.merge(n_games.rename("p2_n_games").to_frame(), how="left", left_on="p2_name", right_index=True)
MIN_STD = 0.05 # alla antas ha minst denna osäkerhet
MAX_STD = 0.15 # högsta osäkerhet
N_GAME_CAP = 10.0 # Har spelaren gjort så här många matcher får den max osäkerhet
df["p1_skill_uncertainty"] = MIN_STD + N_GAME_CAP / df["p1_n_games"].clip_upper(N_GAME_CAP) * (MAX_STD - MIN_STD)
df["p2_skill_uncertainty"] = MIN_STD + N_GAME_CAP / df["p2_n_games"].clip_upper(N_GAME_CAP) * (MAX_STD - MIN_STD)

df.loc[df["p1_skill_uncertainty"].isna(), "p1_skill_uncertainty"] = MAX_STD
df.loc[df["p2_skill_uncertainty"].isna(), "p2_skill_uncertainty"] = MAX_STD

"""
