import arrow
from tankbot.analysis import Mood
from tankbot.analysis.tank import Matchup
from tankbot.api import Result


def test_mood_my_team_win():
    # my team wins
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=5, away_score=2, overtime=False)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.BAD

    game = Result(time=arrow.now(), home="mtl", away="van", home_score=5, away_score=2, overtime=False)
    m = Matchup(game, my_team_involved=True, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.BAD


def test_mood_my_team_ot_win():
    # my team wins in OT against a team in range
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=5, away_score=2, overtime=True)
    m = Matchup(game, my_team_involved=True, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.WORST

    # my team wins in OT
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=5, away_score=2, overtime=True)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.BAD


def test_mood_my_team_ot_loss():
    # my team loses in OT against a team in range
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=5, overtime=True)
    m = Matchup(game, my_team_involved=True, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GOOD

    # my team loses in OT against a team not in range
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=5, overtime=True)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GOOD


def test_mood_my_team_loss():
    # my team loses
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=5, overtime=False)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GREAT

    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=5, overtime=False)
    m = Matchup(game, my_team_involved=True, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GREAT


def test_mood_ideal_team_wins():
    # ideal team wins
    game = Result(time=arrow.now(), home="cgy", away="van", home_score=5, away_score=2, overtime=False)
    m = Matchup(game)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.GOOD

    game = Result(time=arrow.now(), home="cgy", away="van", home_score=5, away_score=2, overtime=False)
    m = Matchup(game, both_in_range=True)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.GOOD


def test_mood_ideal_team_ot_win():
    # ideal team wins
    game = Result(time=arrow.now(), home="cgy", away="van", home_score=5, away_score=2, overtime=True)
    m = Matchup(game)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.GOOD

    game = Result(time=arrow.now(), home="cgy", away="van", home_score=5, away_score=2, overtime=True)
    m = Matchup(game, both_in_range=True)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.GREAT


def test_mood_ideal_team_ot_loss():
    # ideal team wins
    game = Result(time=arrow.now(), home="cgy", away="van", home_score=2, away_score=5, overtime=True)
    m = Matchup(game)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.WORST

    game = Result(time=arrow.now(), home="cgy", away="van", home_score=2, away_score=5, overtime=True)
    m = Matchup(game, both_in_range=True)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.BAD


def test_mood_ideal_team_loss():
    # ideal team wins
    game = Result(time=arrow.now(), home="cgy", away="van", home_score=2, away_score=5, overtime=False)
    m = Matchup(game)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.WORST

    game = Result(time=arrow.now(), home="cgy", away="van", home_score=2, away_score=5, overtime=False)
    m = Matchup(game, both_in_range=True)
    m.ideal_winner = "cgy"
    assert m.get_mood() == Mood.WORST
