from attr import attrib, attrs

from . import BaseMatchup, Cheer, Mood
from ..api import Result


@attrs(slots=True)
class Matchup(BaseMatchup):
    game = attrib()
    ideal_winner = attrib(init=False)
    both_in_range = attrib(default=False)
    my_team_involved = attrib(default=False)
    time = attrib(init=False)

    def __attrs_post_init__(self):
        self.time = self.game.time.format("HH:mm")

    def get_cheer(self):
        return Cheer(self.ideal_winner, self.both_in_range and not self.my_team_involved)

    def get_mood(self):
        if not isinstance(self.game, Result):
            raise ValueError("cannot compute mood on a non-result")

        if self.my_team_involved:
            if self.ideal_winner != self.game.winner:
                # my team won
                if self.both_in_range and self.game.overtime:
                    # the other team is in range and the game went to OT
                    return Mood.WORST
                return Mood.BAD
            else:
                # my team lost
                if self.game.overtime:
                    # the game went to OT
                    return Mood.GOOD
                return Mood.GREAT
        else:
            if self.ideal_winner != self.game.winner:
                # ideal team did not win
                if self.both_in_range and self.game.overtime:
                    # the game went to overtime and the ideal team still got a point
                    return Mood.BAD
                return Mood.WORST
            else:
                # ideal team won
                if self.both_in_range and self.game.overtime:
                    # the other team is in range and it got a point
                    return Mood.GREAT
                return Mood.GOOD


@attrs(slots=True)
class Analysis:
    info = attrib()
    my_team = attrib()  # reference to my team
    my_result = attrib(init=False)  # my team's result last night
    results = attrib(init=False)  # results last night
    my_game = attrib(init=False)  # my team's game tonight
    games = attrib(init=False)  # games tonight
    standings = attrib(init=False)  # relevant standings
    reach = attrib(default=10)

    def __attrs_post_init__(self):
        self.my_result, self.results = self._compute_matchups(self.info.results, past=True)
        self.my_game, self.games = self._compute_matchups(self.info.games)
        self.standings = [s for s in self.info.standings if self._is_team_in_range(s.team)]

    def _is_team_in_range(self, other, past=False):
        if self.my_team == other:
            return True
        my_points = self.info.get_standing(self.my_team, past).points
        other_points = self.info.get_standing(other, past).points
        return other_points <= my_points or abs(other_points - my_points) <= self.reach

    def _is_game_relevant(self, game, past=False):
        return self._is_team_in_range(game.home, past) or self._is_team_in_range(game.away, past)

    def _compute_matchups(self, games, past=False):
        my_matchup = False
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

    def _matchup_from_game(self, game, past=False):
        m = Matchup(game)

        m.both_in_range = self._is_team_in_range(game.away) and self._is_team_in_range(game.home)
        m.my_team_involved = game.away == self.my_team or game.home == self.my_team

        if game.home == self.my_team:
            m.ideal_winner = game.away
        elif game.away == self.my_team:
            m.ideal_winner = game.home
        else:
            # finds the closest team in the standings to our team
            my_points = self.info.get_standing(self.my_team, past=past).points
            points_team = [(self.info.get_standing(t, past=past).points, t) for t in (game.away, game.home)]
            _, closest_t = min(points_team, key=lambda s: abs(s[0] - my_points))
            m.ideal_winner = closest_t
        return m
