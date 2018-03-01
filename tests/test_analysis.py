import arrow

from tankbot.api import Result
from tankbot.analysis import Matchup, Mood


def test_mood_worst():
    """
    - My team wins
    - Other tanker loses
    """
    # MTL wins 5-2
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=5, away_score=2, overtime=False)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.WORST

    game = Result(time=arrow.now(), home="mtl", away="van", home_score=5, away_score=2, overtime=False)
    m = Matchup(game, my_team_involved=True, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.WORST

    # VAN loses 5-2
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=5, away_score=2, overtime=False)
    m = Matchup(game)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.WORST


def test_mood_passable():
    """
    - My team loses in OT
    - Other tanker loses in OT
    """
    # MTL loses in OT 2-3
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=3, overtime=True)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.PASSABLE

    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=3, overtime=True)
    m = Matchup(game, my_team_involved=True, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.PASSABLE

    # VAN loses in OT 2-3
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=3, away_score=2, overtime=True)
    m = Matchup(game)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.PASSABLE


def test_mood_good():
    """
    - My team loses
    - Other tanker wins, OT or not
    """
    # VAN wins 3-2
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=3, overtime=False)
    m = Matchup(game, my_team_involved=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GOOD

    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=3, overtime=False)
    m = Matchup(game, my_team_involved=True, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GOOD

    # VAN wins 3-2
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=3, overtime=False)
    m = Matchup(game)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GOOD

    # VAN wins 3-2 OT
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=2, away_score=3, overtime=True)
    m = Matchup(game)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.GOOD


def test_mood_almost_perfect():
    """
    - Two tankers go to OT but the ideal winner does not win
    """
    # MTL wins 3-2
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=3, away_score=2, overtime=True)
    m = Matchup(game, both_in_range=True)
    m.ideal_winner = "van"
    assert m.get_mood() == Mood.ALMOST_PERFECT


def test_mood_perfect():
    """
    - Two tankers go to OT but the ideal winner does not win
    """
    # MTL wins 3-2
    game = Result(time=arrow.now(), home="mtl", away="van", home_score=3, away_score=2, overtime=True)
    m = Matchup(game, both_in_range=True)
    m.ideal_winner = "mtl"
    assert m.get_mood() == Mood.PERFECT
