from attr import attrs, attrib


@attrs(slots=True)
class Matchup:
    game = attrib()
    tanker = attrib(init=False)
    ideal_winner = attrib(init=False)
    overtime = attrib(default=False)
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
    reach = attrib(default=5)

    def __attrs_post_init__(self):
        self.my_result, self.results = self._compute_matchups(self.info.results)
        self.my_game, self.games = self._compute_matchups(self.info.games)
        self.standings = [s for s in self.info.standings if self.is_team_in_range(s.team)]

    def is_team_in_range(self, other):
        if self.my_team == other:
            return True
        return (other.standing.points <= self.my_team.standing.points or
                abs(other.standing.points - self.my_team.standing.points) <= self.reach)

    def is_game_relevant(self, game):
        return self.is_team_in_range(game.home) or self.is_team_in_range(game.away)

    def _compute_matchups(self, games):
        my_matchup = False
        matchups = []

        for game in games:
            if not self.is_game_relevant(game):
                continue
            m = self._matchup_from_game(game)

            if self.my_team == game.home or self.my_team == game.away:
                my_matchup = m
            else:
                matchups.append(m)

        return my_matchup, matchups

    def _matchup_from_game(self, game):
        m = Matchup(game)

        if game.home == self.my_team:
            m.tanker = game.home
            m.ideal_winner = game.away
        elif game.away == self.my_team:
            m.tanker = game.away
            m.ideal_winner = game.home
        else:
            if self.is_team_in_range(game.home) and self.is_team_in_range(game.away):
                m.overtime = True
            m.tanker = min((game.home, game.away), key=lambda team: team.standing.points)
            m.ideal_winner = m.tanker
        return m
