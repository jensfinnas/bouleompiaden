from flask import Flask, jsonify, Response, make_response, render_template, abort
from flask_jsglue import JSGlue
from dicttoxml import dicttoxml
from urllib.parse import unquote
import csv
import json
import io
import os
from slugify import slugify

from modules.simulate import game
from modules import  players
from settings import TRUE_SKILL_BASE, PLAYER_DATA_DIR

app = Flask(__name__)
jsglue = JSGlue(app)

#if STAGE in ["dev", "production"]:
#    url_prefix = "/" + STAGE
#else:
#    url_prefix = ""


@app.route("/", methods=["GET"])
def site_index():
    all_players = players.all()
    # Hackishly remove all players without both first and last name
    allowed_first_names = ["Robeson", "Estrid"]
    all_players = [x for x in all_players if (" " in x["name"]) or
                                             (x["name"] in allowed_first_names)]

    context = {
        "players": all_players,
        "base_skill": TRUE_SKILL_BASE,
    }
    # number of players etc.
    context.update(players.metadata)

    return render_template('index.html', **context)

@app.route("/spelare/<player_slug>", methods=["GET"])
def player_index(player_slug):
    context = {}
    try:
        context["player"] = players.get(player_slug)
    except:
        abort(404)
    
    context.update(players.metadata)

    return render_template('player.html', **context)

@app.route("/turnering/<year>", methods=["GET"])
def tournament_index(year):
    context = {}
    file_path = os.path.join("data", "tournaments", f"{year}.json")
    
    if not os.path.exists(file_path):
        abort(404)

    with open(file_path) as f:
        context["tournament"] = json.load(f)
    
    context.update(players.metadata)

    return render_template('tournament.html', **context)


def get_simulation_data(player1, player2):
    """Sets up data context for a simulated game between two players.
    """
    player1, player2 = unquote(player1), unquote(player2)
    resp = game(player1, player2)
    context = {
        "player1": {
            "name": player1,
            #"wins": resp["p1_wins"],
            "win_prob": resp["p1_win_prob"],
            "skill": resp["p1"]["rating"].mu,
            "skill_rank": resp["p1"]["skill_rank"],
            "skill_history": resp["p1"]["skill_history"],
            "n_games": resp["p1"]["n_games"],
            "years": resp["p1"]["years"],
            "historical_wins": resp["p1"]["n_wins"],
            "historical_win_rate": resp["p1"]["win_rate"],
            "historical_score_share": resp["p1"]["score_share"],
        },
        "player2": {
            "name": player2,
            "win_prob": resp["p2_win_prob"],
            "skill": resp["p2"]["rating"].mu,
            "skill_rank": resp["p2"]["skill_rank"],
            "skill_history": resp["p2"]["skill_history"],
            "n_games": resp["p2"]["n_games"],
            "years": resp["p2"]["years"],
            "historical_wins": resp["p2"]["n_wins"],
            "historical_win_rate": resp["p2"]["win_rate"],
            "historical_score_share": resp["p2"]["score_share"],
        },
    }
    context["previous_games"] = players.previous_mutual_games(player1, player2)

    if resp["p1_win_prob"] > resp["p2_win_prob"]:
        context["winner"] = context["player1"]
        context["loser"] = context["player2"]
    else:
        context["winner"] = context["player2"]
        context["loser"] = context["player1"]

    return context


@app.route("/<fmt>/<player1>/vs/<player2>", methods=["GET"])
def simulate(fmt, player1, player2):
    context = get_simulation_data(player1, player2)

    if fmt == "json":
        return jsonify(context)

    elif fmt == "html":
        return render_template("result.html", **context)

    elif fmt == "csv":
        rows = []
        rows.append(["Antal simulerade spel", context["n_games"]])
        rows.append([])


        keys = ["name", "wins", "win_prob", "skill", "skill_sigma"]
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
            "skill_sigma": "Osäkerhet på skill",
            "n_games": "Antal matcher",
            "historical_wins": "Antal vinster",
            "historical_win_rate": "Andel vinster",
            "historical_score_share": "Poängandel i snitt",
        }[key]
    except KeyError:
        return key

@app.template_filter('slugify')
def slugify_filter(s):
    return slugify(s)

@app.template_filter('genitive')
def genitive_filter(s):
    """
    genitive_filter("Lars") => "Lars"
    genitive_filter("Kalle") => "Kalles"
    """
    if s.endswith("s"):
        return s
    else:
        return s + "s"
