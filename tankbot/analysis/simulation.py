import copy
import random
from collections import defaultdict
from enum import Enum

from attr import attrib, attrs

from tankbot.api import Standing


class Outcome(Enum):
    WIN = 1
    LOSS = 2
    OT = 3

    def wins(self):
        if self == Outcome.WIN:
            return 1
        return 0

    def losses(self):
        if self == Outcome.LOSS:
            return 1
        return 0

    def ot(self):
        if self == Outcome.OT:
            return 1
        return 0

    def points(self):
        if self == Outcome.WIN:
            return 2
        elif self == Outcome.LOSS:
            return 0
        elif self == Outcome.OT:
            return 1


@attrs
class Odds:
    win = attrib()
    loss = attrib()
    ot = attrib()

    @classmethod
    def from_standing(cls, standing: Standing):
        return Odds(
            standing.wins / standing.gamesPlayed,
            standing.losses / standing.gamesPlayed,
            standing.ot / standing.gamesPlayed,
        )

    def random_event(self):
        return random.choices([Outcome.WIN, Outcome.LOSS, Outcome.OT], weights=[self.win, self.loss, self.ot])[0]


class Simulation:
    def __init__(self, standings):
        self.orig = standings
        self.work = [copy.copy(s) for s in standings]
        self.divisions = defaultdict(list)
        self.conferences = defaultdict(list)
        self.playoffs = defaultdict(list)
        self.playoffs_teams = set()

    def _standings_sort_key(self, standing):
        return (standing.points, standing.wins)

    def reset(self):
        for orig, work in zip(self.orig, self.work):
            work.gamesPlayed = orig.gamesPlayed
            work.points = orig.points
            work.wins = orig.wins
            work.losses = orig.losses
            work.ot = orig.ot

        for d in self.divisions.values():
            d.clear()

        for c in self.conferences.values():
            c.clear()

        for x in self.playoffs.values():
            x.clear()

        self.playoffs_teams.clear()

    def run(self):
        self.reset()

        standings = self.work
        for standing in standings:
            odds = Odds.from_standing(standing)
            while standing.gamesPlayed < 82:
                standing.gamesPlayed += 1
                event = odds.random_event()
                standing.points += event.points()
                standing.wins += event.wins()
                standing.losses += event.losses()
                standing.ot += event.ot()

        for standing in standings:
            self.divisions[standing.team.division].append(standing)
            self.conferences[standing.team.conference].append(standing)

        for div in self.divisions.values():
            div.sort(key=self._standings_sort_key, reverse=True)

        for conf in self.conferences.values():
            conf.sort(key=self._standings_sort_key, reverse=True)

        for div in self.divisions.values():
            for standing in div[:3]:
                self.playoffs[standing.team.conference].append(standing)
                self.playoffs_teams.add(standing.team)

        for conf in self.conferences.values():
            for standing in conf:
                ls = self.playoffs[standing.team.conference]
                if len(ls) < 8 and standing.team not in self.playoffs_teams:
                    ls.append(standing)
                    self.playoffs_teams.add(standing.team)

    def print_standings(self):
        for name, standings in self.playoffs.items():
            print("Division:", name)
            for standing in standings:
                print(standing.team.name, standing.points)
            print()


def _add_game(team, standings, points):
    for standing in standings:
        if standing.team == team:
            standing.gamesPlayed += 1
            standing.points += points


def _simulate(team, standings):
    x = 0
    sim = Simulation(standings)
    for i in range(5000):
        sim.run()
        if team in sim.playoffs_teams:
            x += 1
    return x


def pick_ideal_winner(my_team, game, standings):
    home_win_standings = [copy.copy(s) for s in standings]
    _add_game(game.home, home_win_standings, 2)
    _add_game(game.away, home_win_standings, 0)
    home_win_x = _simulate(my_team, home_win_standings)

    away_win_standings = [copy.copy(s) for s in standings]
    _add_game(game.away, away_win_standings, 2)
    _add_game(game.home, away_win_standings, 0)
    away_win_x = _simulate(my_team, away_win_standings)

    print("{}({}) at {}({})".format(game.away.name, away_win_x, game.home.name, home_win_x))

    if home_win_x > away_win_x:
        return game.home
    else:
        return game.away
