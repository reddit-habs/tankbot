from enum import Enum

from attr import attrib, attrs, evolve

from . import BaseMatchup, Cheer, Mood
from ..api import Game, Info, Result, Team
from .simulation import pick_ideal_winner


class Outlook(Enum):
    TOP = 1
    WILDCARD = 2
    OUTSIDE = 3


@attrs(slots=True)
class Matchup(BaseMatchup):
    game = attrib()
    ideal_winner = attrib(init=False)
    my_team_involved = attrib(default=False)
    time = attrib(init=False)

    def __attrs_post_init__(self):
        self.time = self.game.time.format("HH:mm")

    def get_cheer(self):
        return Cheer(self.ideal_winner, False)

    def get_mood(self):
        if not isinstance(self.game, Result):
            raise ValueError("cannot compute mood on a non-result")

        if self.ideal_winner != self.game.winner:
            # ideal team did not win
            if self.my_team_involved and self.game.overtime:
                # our team did not win but got an OT points
                return Mood.BAD
            return Mood.WORST
        else:
            # ideal team won
            if self.game.overtime:
                # other team got an OT point and it's in the conference
                return Mood.GOOD
            return Mood.GREAT


@attrs(slots=True)
class PlayoffsMatchup:
    high_team = attrib()
    low_team = attrib()


class GameAnalysis:
    def __init__(self, a, game: Game, past=False):
        self.a = a
        self.game = game
        self.past = past
        self.standings = self.a.info.past_standings if past else a.info.standings

        self.my_team_points = self.a.info.get_standing(self.a.my_team, past).points
        self.home_points = self.a.info.get_standing(game.home, past).points
        self.away_points = self.a.info.get_standing(game.away, past).points

        self.home_diff = abs(self.my_team_points - self.home_points)
        self.away_diff = abs(self.my_team_points - self.away_points)

        self.my_team_involed = game.home == self.a.my_team or game.away == self.a.my_team

        self.home_in_conf = game.home in self.a.own_conference_teams
        self.away_in_conf = game.away in self.a.own_conference_teams

        self.home_in_reach = self.home_diff <= self.a.reach
        self.away_in_reach = self.away_diff <= self.a.reach

        self.home_in_conf_reach = self.home_in_conf and self.home_in_reach
        self.away_in_conf_reach = self.away_in_conf and self.away_in_reach

    def is_relevant(self):
        if self.my_team_involed:
            return True

        if self.game.home not in self.a.own_conference_teams and self.game.away not in self.a.own_conference_teams:
            return False

        else:
            return self.home_in_conf_reach or self.away_in_conf_reach

    def _furthest_team(self):
        if self.home_diff < self.away_diff:
            return self.game.away
        else:
            return self.game.home

    def get_matchup(self):
        m = Matchup(self.game)
        m.my_team_involved = self.my_team_involed
        m.other_in_conference = True

        if self.my_team_involed:
            m.ideal_winner = self.a.my_team
        elif self.game.home in self.a.own_conference_teams and self.game.away not in self.a.own_conference_teams:
            m.ideal_winner = self.game.away
        elif self.game.away in self.a.own_conference_teams and self.game.home not in self.a.own_conference_teams:
            m.ideal_winner = self.game.home
        else:
            m.ideal_winner = pick_ideal_winner(self.a.my_team, self.game, self.standings)

        return m


class Analysis:
    def __init__(self, info: Info, my_team: Team, reach=10):
        self.info = info
        self.my_team = my_team
        self.reach = reach

        self.own_division = []  # ordered list of all the team's standings in our division
        self.other_division = []  # ordered list of all the team's standings in the other division
        self.wildcard = []  # ordered list of wild card team's standings

        self.own_conference_teams = set()

        # create the standings lists

        place = 1

        for standing in self.info.standings:
            if standing.team.conference == self.my_team.conference:
                self.own_conference_teams.add(standing.team)
                if standing.team.division == self.my_team.division:
                    self.own_division.append(evolve(standing, place=place, seed=len(self.own_division) + 1))
                    if len(self.own_division) > 3:
                        self.wildcard.append(evolve(standing, place=place, seed=len(self.wildcard) + 1))
                else:
                    self.other_division.append(evolve(standing, place=place, seed=len(self.other_division) + 1))
                    if len(self.other_division) > 3:
                        self.wildcard.append(evolve(standing, place=place, seed=len(self.wildcard) + 1))
                place += 1

        # calculate results and matchups

        self.my_result, self.results = self._compute_matchups(self.info.results, past=True)
        self.my_game, self.games = self._compute_matchups(self.info.games)

        self.playoffs_matchups = self._compute_playoffs_matchups()

    def _compute_matchups(self, games, past=False):
        my_matchup = None
        matchups = []

        for game in games:
            ga = GameAnalysis(self, game, past)
            if ga.is_relevant():
                m = ga.get_matchup()
                if self.my_team == game.home or self.my_team == game.away:
                    my_matchup = m
                else:
                    matchups.append(m)

        return my_matchup, matchups

    def _compute_playoffs_matchups(self):
        tops = [self.own_division[0], self.other_division[0]]
        tops.sort(key=lambda s: s.points, reverse=True)
        return [
            PlayoffsMatchup(high_team=tops[0], low_team=self.wildcard[1]),
            PlayoffsMatchup(high_team=tops[1], low_team=self.wildcard[0]),
            PlayoffsMatchup(high_team=self.own_division[1], low_team=self.own_division[2]),
            PlayoffsMatchup(high_team=self.other_division[1], low_team=self.other_division[2]),
        ]
