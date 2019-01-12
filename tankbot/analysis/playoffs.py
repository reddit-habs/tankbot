from attr import attrib, attrs, evolve

from . import BaseMatchup, Cheer, Mood
from ..api import Result


@attrs(slots=True)
class Matchup(BaseMatchup):
    game = attrib()
    ideal_winner = attrib(init=False)
    my_team_involved = attrib(default=False)
    other_in_conference = attrib(default=False)
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
            if self.other_in_conference and self.game.overtime:
                # other team got an OT point and it's in the conference
                return Mood.GOOD
            return Mood.GREAT


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
        self.my_team_top3 = False

        for standing in self.info.standings:
            if standing.team.conference == self.my_team.conference:
                self._conference_teams.add(standing.team)
                if standing.team.division == self.my_team.division:
                    self._own_division_teams.add(standing.team)
                    if len(self.own_division) < 3:
                        if standing.team == self.my_team:
                            self.my_team_top3 = True
                        self.own_division.append(evolve(standing, place=len(self.own_division) + 1))
                    else:
                        self.wildcard.append(evolve(standing, place=len(self.wildcard) + 1))
                else:
                    if len(self.other_division) < 3:
                        self.other_division.append(evolve(standing, place=len(self.other_division) + 1))
                    else:
                        self.wildcard.append(evolve(standing, place=len(self.wildcard) + 1))

        self.my_result, self.results = self._compute_matchups(self.info.results, past=True)
        self.my_game, self.games = self._compute_matchups(self.info.games)

    def _is_game_relevant(self, game, past=False):
        my_points = self.info.get_standing(self.my_team, past).points
        return (
            game.home in self._conference_teams
            and abs(self.info.get_standing(game.home).points - my_points) <= self.reach
        ) or (
            game.away in self._conference_teams
            and abs(self.info.get_standing(game.away).points - my_points) <= self.reach
        )

    def _are_both_in_division(self, game, past=False):
        return game.home in self._own_division_teams and game.away in self._own_division_teams

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
        my_points = self.info.get_standing(self.my_team, past=past).points
        points_team = [(self.info.get_standing(t, past=past).points, t) for t in (game.away, game.home)]
        _, furthest_t = max(points_team, key=lambda s: abs(s[0] - my_points))
        return furthest_t

    def _matchup_from_game(self, game, past=False):
        m = Matchup(game)
        m.my_team_involved = game.away == self.my_team or game.home == self.my_team

        if m.my_team_involved:
            m.ideal_winner = self.my_team
        else:
            both_in_division = self._are_both_in_division(game, past)

            # Default case. We usually want the team furthest away from us in points to win.
            m.ideal_winner = self._find_furtest_team(game, past)

            if self._are_both_in_conference(game) and not both_in_division:
                # Both teams are in the conference, but one isn't in the division.
                if self.my_team_top3:
                    # If we're top 3 in the division, we want the team in our division to lose.
                    if game.away in self._own_division_teams:
                        m.ideal_winner = game.home
                    elif game.home in self._own_division_teams:
                        m.ideal_winner = game.away
            elif not both_in_division:
                # One of the team is in the conference, but the other isn't.
                m.other_in_conference = True
                if game.away in self._conference_teams:
                    m.ideal_winner = game.home
                elif game.home in self._conference_teams:
                    m.ideal_winner = game.away
                else:
                    raise ValueError("invalid state")
        return m
