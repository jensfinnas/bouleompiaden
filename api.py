from flask import Flask, jsonify, Response, make_response, render_template
from flask_jsglue import JSGlue
from dicttoxml import dicttoxml
from urllib.parse import unquote
import csv
import io

from modules.simulate import game
from modules import  players
from settings import STAGE

app = Flask(__name__)
jsglue = JSGlue(app)

@app.route("/", methods=["GET"])
def index():
    all_players = players.all()
    # Hackishly remove all players without both first and last name
    all_players = [x for x in all_players if " " in x]

    context = {
        "players": all_players
    }


    # Hack: The urls for the ajax calls has to be prepended with a the stage
    # when deployed to AWS Lambda
    if STAGE == "local":
        context["url_prefix"] = ""
    elif STAGE in ["dev", "production"]:
        context["url_prefix"] = STAGE
    else:
        raise Exception("Invalid stage: {}".format(STAGE))


    return render_template('index.html', **context)

def get_context(player1, player2):
    """Sets up data context for a simulated game between two players
    """
    n_games = 1000
    player1, player2 = unquote(player1), unquote(player2)
    resp = game(player1, player2, n_games=n_games)

    context = {
        "player1": {
            "name": player1,
            "wins": resp["p1_wins"],
            "win_prob": resp["p1_win_prob"],
            "skill": resp["p1"]["skill"],
            "skill_uncertainty": resp["p1"]["skill_uncertainty"],
            "n_games": resp["p1"]["n_games"],
            "historical_wins": resp["p1"]["n_wins"],
            "historical_win_rate": resp["p1"]["win_rate"],
            "historical_score_share": resp["p1"]["score_share"],
        },
        "player2": {
            "name": player2,
            "wins": resp["p2_wins"],
            "win_prob": resp["p2_win_prob"],
            "skill": resp["p2"]["skill"],
            "skill_uncertainty": resp["p2"]["skill_uncertainty"],
            "n_games": resp["p2"]["n_games"],
            "historical_wins": resp["p2"]["n_wins"],
            "historical_win_rate": resp["p2"]["win_rate"],
            "historical_score_share": resp["p2"]["score_share"],
        },
        "n_games": n_games,
        "diff_counts": resp["diff_counts"],
        "most_likely_diff": resp["most_likely_diff"],
        # most common results
        "results": resp["result_counts"].head(10).reset_index().values.tolist()
    }
    if resp["p1_win_prob"] > resp["p2_win_prob"]:
        context["winner"] = context["player1"]
        context["loser"] = context["player2"]
    else:
        context["winner"] = context["player2"]
        context["loser"] = context["player1"]

    return context


@app.route("/<fmt>/<player1>/vs/<player2>", methods=["GET"])
def simulate(fmt, player1, player2):
    context = get_context(player1, player2)

    if fmt == "json":
        return jsonify(context)

    elif fmt == "html":
        return render_template("result.html", **context)

    elif fmt == "csv":
        rows = []
        rows.append(["Antal simulerade spel", context["n_games"]])
        rows.append([])


        keys = ["name", "wins", "win_prob", "skill", "skill_uncertainty"]
        for key in keys:
            row = [translate(key), context["player1"][key], context["player2"][key]]
            rows.append(row)

        rows.append([])
        rows.append(["Mest sannolika resultat"])
        rows.append(["Resultat", "Antal utfall (av {})".format(context["n_games"])])
        for result, count in context["results"]:
            rows.append(["'{}".format(result), count])

        rows.append([])
        rows.append(["Historiska stats"])
        keys = ["name", "n_games", "historical_wins", "historical_win_rate", "historical_score_share"]
        for key in keys:
            row = [translate(key), context["player1"][key], context["player2"][key]]
            rows.append(row)

        csv_string = io.StringIO()
        writer = csv.writer(csv_string)
        writer.writerows(rows)

        output = make_response(csv_string.getvalue())

        return output

    elif fmt == "xml":
        xml = dicttoxml(context)
        return Response(xml, content_type='text/xml; charset=utf-8')
    else:
        return "Bad format: {}".format(fmt)

def translate(key):
    try:
        return {
            "name": "Spelare",
            "wins": "Antal förväntade vinster",
            "win_prob": "Vinstchans",
            "skill": "Skill (0-1)",
            "skill_uncertainty": "Osäkerhet på skill",
            "n_games": "Antal matcher",
            "historical_wins": "Antal vinster",
            "historical_win_rate": "Andel vinster",
            "historical_score_share": "Poängandel i snitt",
        }[key]
    except KeyError:
        return key
