from attr import attrib, attrs

from .api import CachedInfo, Team
from .generate import generate


@attrs
class Matchup:
    game = attrib()
    tanker = attrib(default=None)
    overtime = attrib(default=False)
    time = attrib(init=False)

    def __attrs_post_init__(self):
        self.time = self.game.time.format('HH:mm')

    @classmethod
    def from_game(cls, game, my_team):
        m = Matchup(game)
        my_standing = my_team.standing
        home_standing = game.home.standing
        away_standing = game.away.standing

        if game.home == my_team:
            m.tanker = game.away
        elif game.away == my_team:
            m.tanker = game.home
        elif home_standing.points <= my_standing.points and away_standing.points <= my_standing.points:
            m.overtime = True
        elif home_standing.points <= my_standing.points:
            m.tanker = game.home
        elif away_standing.points <= my_standing.points:
            m.tanker = game.away
        else:
            winner, _ = min([(game.home, home_standing), (game.away, away_standing)], key=lambda pair: pair[1].points)
            m.tanker = winner
        return m


def is_team_in_range(my_team, other):
    if my_team == other:
        return True
    return other.standing.points <= my_team.standing.points or abs(other.standing.points - my_team.standing.points) <= 5


def is_game_relevant(game, my_team: Team):
    if my_team == game.home or my_team == game.away:
        return True

    return is_team_in_range(my_team, game.home) or is_team_in_range(my_team, game.away)


def compute_matchups(my_team: Team, games):
    my_matchup = False
    matchups = []

    for game in games:
        if not is_game_relevant(game, my_team):
            continue
        m = Matchup.from_game(game, my_team)

        if my_team == game.home or my_team == game.away:
            my_matchup = m
        else:
            matchups.append(m)

    return my_matchup, matchups


if __name__ == '__main__':
    info = CachedInfo()
    with open('template.md') as f:
        my_team = info.get_team_by_code('mtl')
        my_matchup, matchups = compute_matchups(my_team, info.games)
        my_result, results = compute_matchups(my_team, info.results)
        standings = [s for s in info.standings if is_team_in_range(my_team, s.team)]
        print('\n'.join(generate(my_result, results, my_matchup, matchups, standings)))
