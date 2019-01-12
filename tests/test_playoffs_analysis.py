import os

import arrow

from tankbot import serde
from tankbot.analysis import Mood
from tankbot.analysis.playoffs import Analysis, Matchup
from tankbot.api import Result

INFO0 = serde.loadf(os.path.join(os.path.dirname(__file__), "info0.json"))
INFO1 = serde.loadf(os.path.join(os.path.dirname(__file__), "info1.json"))


def find_matchup_with_teams(matchups, t1, t2):
    t1 = t1.lower()
    t2 = t2.lower()
    for m in matchups:
        s = set([m.game.away.code.lower(), m.game.home.code.lower()])
        if t1 in s and t2 in s:
            return m
    return None


def test_ideal_winner_my_team():
    my_team = INFO0.get_team_by_code("mtl")
    a = Analysis(INFO0, my_team)
    assert a.my_game.ideal_winner == my_team


def test_ideal_winner_both_in_division():
    my_team = INFO0.get_team_by_code("mtl")
    a = Analysis(INFO0, my_team)
    g = find_matchup_with_teams(a.games, "buf", "tbl")
    assert g.ideal_winner == INFO0.get_team_by_code("tbl")

    a = Analysis(INFO0, my_team)
    g = find_matchup_with_teams(a.games, "bos", "tor")
    assert g.ideal_winner == INFO0.get_team_by_code("tor")


def test_ideal_winner_both_out_division():
    my_team = INFO0.get_team_by_code("mtl")
    a = Analysis(INFO0, my_team)
    g = find_matchup_with_teams(a.games, "cbj", "wsh")
    assert g.ideal_winner == INFO0.get_team_by_code("wsh")

    a = Analysis(INFO0, my_team)
    g = find_matchup_with_teams(a.games, "nyr", "nyi")
    assert g.ideal_winner == INFO0.get_team_by_code("nyr")


def test_ideal_winner_one_outside_conf():
    my_team = INFO0.get_team_by_code("mtl")
    a = Analysis(INFO0, my_team, reach=1000)
    g = find_matchup_with_teams(a.games, "det", "min")
    assert g.ideal_winner == INFO0.get_team_by_code("min")

    a = Analysis(INFO0, my_team, reach=1000)
    g = find_matchup_with_teams(a.games, "ott", "sjs")
    assert g.ideal_winner == INFO0.get_team_by_code("sjs")


def test_ideal_winner_when_top3_both_in_division():
    my_team = INFO0.get_team_by_code("tbl")
    a = Analysis(INFO0, my_team, reach=1000)
    g = find_matchup_with_teams(a.games, "tor", "bos")
    assert g.ideal_winner == INFO0.get_team_by_code("bos")


def test_ideal_winner_when_top3_one_outside_division():
    my_team = INFO1.get_team_by_code("tbl")
    a = Analysis(INFO1, my_team, reach=1000)
    g = find_matchup_with_teams(a.games, "wsh", "bos")
    assert g.ideal_winner == INFO1.get_team_by_code("wsh")


def test_ideal_winner_when_top3_both_outside_division():
    my_team = INFO0.get_team_by_code("tbl")
    a = Analysis(INFO0, my_team, reach=1000)
    g = find_matchup_with_teams(a.games, "wsh", "cbj")
    assert g.ideal_winner == INFO0.get_team_by_code("cbj")

    my_team = INFO0.get_team_by_code("wsh")
    a = Analysis(INFO0, my_team, reach=1000)
    g = find_matchup_with_teams(a.games, "tor", "bos")
    assert g.ideal_winner == INFO0.get_team_by_code("bos")


def test_mood_my_team_win():
    # my team wins
    game = Result(time=arrow.now(), home="mtl", away="bos", home_score=5, away_score=2, overtime=False)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "mtl"
    assert m.get_mood() == Mood.GREAT


def test_mood_my_team_ot_win():
    game = Result(time=arrow.now(), home="mtl", away="bos", home_score=5, away_score=2, overtime=True)
    m = Matchup(game, my_team_involved=True, other_in_conference=True)
    m.ideal_winner = "mtl"
    assert m.get_mood() == Mood.GOOD


def test_mood_my_team_loss():
    # my team wins
    game = Result(time=arrow.now(), home="mtl", away="bos", home_score=2, away_score=5, overtime=False)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "mtl"
    assert m.get_mood() == Mood.WORST


def test_mood_my_team_ot_loss():
    game = Result(time=arrow.now(), home="mtl", away="bos", home_score=2, away_score=5, overtime=True)
    m = Matchup(game, my_team_involved=True, other_in_conference=True)
    m.ideal_winner = "mtl"
    assert m.get_mood() == Mood.BAD


def test_mood_ideal_team_win():
    # my team wins
    game = Result(time=arrow.now(), home="tor", away="bos", home_score=5, away_score=2, overtime=False)
    m = Matchup(game, my_team_involved=False)
    m.ideal_winner = "tor"
    assert m.get_mood() == Mood.GREAT


def test_mood_ideal_team_ot_win():
    game = Result(time=arrow.now(), home="tor", away="bos", home_score=5, away_score=2, overtime=True)
    m = Matchup(game, my_team_involved=False, other_in_conference=True)
    m.ideal_winner = "tor"
    assert m.get_mood() == Mood.GOOD


def test_mood_ideal_team_loss():
    # my team wins
    game = Result(time=arrow.now(), home="tor", away="bos", home_score=2, away_score=5, overtime=False)
    m = Matchup(game, my_team_involved=False)
    m.ideal_winner = "tor"
    assert m.get_mood() == Mood.WORST


def test_mood_ideal_team_ot_loss():
    game = Result(time=arrow.now(), home="tor", away="bos", home_score=2, away_score=5, overtime=True)
    m = Matchup(game, my_team_involved=False, other_in_conference=True)
    m.ideal_winner = "tor"
    assert m.get_mood() == Mood.WORST
