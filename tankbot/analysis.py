from attr import attrs, attrib


@attrs(slots=True)
class Matchup:
    game = attrib()
    ideal_winner = attrib(init=False)
    both_in_range = attrib(default=False)
    my_team_involved = attrib(default=False)
    time = attrib(init=False)

    def __attrs_post_init__(self):
        self.time = self.game.time.format('HH:mm')


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
        self.standings = [s for s in self.info.standings if self.is_team_in_range(s.team)]

    def is_team_in_range(self, other, past=False):
        if self.my_team == other:
            return True
        my_points = self.info.get_standing(self.my_team, past).points
        other_points = self.info.get_standing(other, past).points
        return (other_points <= my_points or abs(other_points - my_points) <= self.reach)

    def is_game_relevant(self, game, past=False):
        return self.is_team_in_range(game.home, past) or self.is_team_in_range(game.away, past)

    def _compute_matchups(self, games, past=False):
        my_matchup = False
        matchups = []

        for game in games:
            if not self.is_game_relevant(game, past):
                continue
            m = self._matchup_from_game(game, past)

            if self.my_team == game.home or self.my_team == game.away:
                my_matchup = m
            else:
                matchups.append(m)

        return my_matchup, matchups

    def _matchup_from_game(self, game, past=False):
        m = Matchup(game)

        m.both_in_range = self.is_team_in_range(game.away) and self.is_team_in_range(game.home)
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
