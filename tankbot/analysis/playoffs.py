from attr import attrib, attrs, evolve

from . import BaseMatchup, Cheer, Mood
from ..api import Result


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


class Analysis:
    def __init__(self, info, my_team, reach=10):
        self.info = info
        self.my_team = my_team
        self.reach = reach

        self.own_division = []
        self.other_division = []
        self.wildcard = []

        self._own_division_teams = set()
        self._conference_teams = set()
        self._top_3_teams = set()

        place = 1

        for standing in self.info.standings:
            if standing.team.conference == self.my_team.conference:
                self._conference_teams.add(standing.team)
                if standing.team.division == self.my_team.division:
                    self._own_division_teams.add(standing.team)
                    self.own_division.append(evolve(standing, place=place, seed=len(self.own_division) + 1))
                    if len(self.own_division) <= 3:
                        self._top_3_teams.add(standing.team)
                    else:
                        self.wildcard.append(evolve(standing, place=place, seed=len(self.wildcard) + 1))
                else:
                    self.other_division.append(evolve(standing, place=place, seed=len(self.other_division) + 1))
                    if len(self.other_division) <= 3:
                        self._top_3_teams.add(standing.team)
                    else:
                        self.wildcard.append(evolve(standing, place=place, seed=len(self.wildcard) + 1))
                place += 1

        self.my_result, self.results = self._compute_matchups(self.info.results, past=True)
        self.my_game, self.games = self._compute_matchups(self.info.games)

        self.playoffs_matchups = self._compute_playoffs_matchups()

    def _point_difference(self, other_team, past=False):
        if self.my_team.conference != other_team.conference:
            raise ValueError("teams are not in the same conference")
        if (
            self.my_team.division != other_team.division
            and self.my_team in self._top_3_teams
            and other_team in self._top_3_teams
        ):
            # teams are not in the same division and both are top 3 in their respective divisions
            # the point difference is the sum from each team to the 4th place in their division
            my_points = self.info.get_standing(self.my_team, past).points
            other_points = self.info.get_standing(other_team, past).points

            return abs(my_points - self.info.get_standing(self.own_division[3].team).points) + abs(
                other_points - self.info.get_standing(self.other_division[3].team).points
            )
        return abs(self.info.get_standing(self.my_team).points - self.info.get_standing(other_team).points)

    def _is_game_relevant(self, game, past=False):
        return (game.home in self._conference_teams and self._point_difference(game.home, past) <= self.reach) or (
            game.away in self._conference_teams and self._point_difference(game.away, past) <= self.reach
        )

    def _are_both_in_conference(self, game, past=False):
        return game.home in self._conference_teams and game.away in self._conference_teams

    def _compute_matchups(self, games, past=False):
        my_matchup = None
        matchups = []

        for game in games:
            if not self._is_game_relevant(game, past):
                continue
            m = self._matchup_from_game(game, past)

            if self.my_team == game.home or self.my_team == game.away:
                my_matchup = m
            else:
                matchups.append(m)

        return my_matchup, matchups

    def _find_furtest_team(self, game, past=False):
        points_team = [(self._point_difference(t, past), t) for t in (game.away, game.home)]
        _, furthest_t = max(points_team, key=lambda s: s[0])
        return furthest_t

    def _matchup_from_game(self, game, past=False):
        m = Matchup(game)
        m.my_team_involved = game.away == self.my_team or game.home == self.my_team

        if m.my_team_involved:
            m.ideal_winner = self.my_team
        else:
            if self._are_both_in_conference(game):
                # Default case. We usually want the team furthest away from us in points to win.
                m.ideal_winner = self._find_furtest_team(game, past)
            else:
                # One of the team is in the conference, but the other isn't.
                if game.away in self._conference_teams:
                    m.ideal_winner = game.home
                elif game.home in self._conference_teams:
                    m.ideal_winner = game.away
                else:
                    raise ValueError("invalid state")
        return m

    def _compute_playoffs_matchups(self):
        tops = [self.own_division[0], self.other_division[0]]
        tops.sort(key=lambda s: s.points, reverse=True)
        return [
            PlayoffsMatchup(high_team=tops[0], low_team=self.wildcard[1]),
            PlayoffsMatchup(high_team=tops[1], low_team=self.wildcard[0]),
            PlayoffsMatchup(high_team=self.own_division[1], low_team=self.own_division[2]),
            PlayoffsMatchup(high_team=self.other_division[1], low_team=self.other_division[2]),
        ]
