# Is this a good idea? Probably not.


def _underline_header(header):
    return "|".join([":---:"] * len(header.split('|')))


def _get_mood(r):
    # if should have went to overtime and it did, perfect
    if r.overtime and r.game.overtime:
        return "Perfect"
    # if the enemy tanker won
    elif r.tanker == r.game.winner:
        return "Yes"
    # if the enemy tanker didn't win but went to OT
    elif r.overtime:
        return "Half yay"
    # no win, no OT
    else:
        return "No"


def _generate_result_line(r):
    yield "[](/r/{}) at [](/r/{})|{}-{} [](/r/{}) {}|{}".format(
        r.game.away.subreddit,
        r.game.home.subreddit,
        r.game.away_score,
        r.game.home_score,
        r.game.winner.subreddit,
        "OT" if r.game.overtime else "",
        _get_mood(r),
    )


def _generate_game_line(r):
    yield "[](/r/{}) at [](/r/{})|{}|{}".format(
        r.game.away.subreddit,
        r.game.home.subreddit,
        "OT" if r.overtime else '[](/r/{})'.format(r.tanker.subreddit),
        r.time,
    )


def _generate_standings(standings):
    header = "Place|Team|GP|Record|Points|ROW"
    header_lines = _underline_header(header)
    yield "## Standings"
    yield ""
    yield header
    yield header_lines
    for s in standings:
        yield "{}|[](/r/{})|{}|{}|{}|{}".format(
            s.place,
            s.team.subreddit,
            s.gamesPlayed,
            "{:02}-{:02}-{:02}".format(s.wins, s.losses, s.ot),
            s.points,
            s.row,
        )
    yield ""


def _generate_tank_section(my, lst, title, header, func):
    header_lines = _underline_header(header)
    yield "## {}".format(title)
    yield ""
    yield "- De Tanque:"
    yield ""
    if my:
        yield header
        yield header_lines
        yield from func(my)
    else:
        yield "Nothing."
    yield ""
    yield "- Out of town tank:"
    yield ""
    if len(lst) > 0:
        yield header
        yield header_lines
        for entry in lst:
            yield from func(entry)
    else:
        yield "Nothing out of town."
    yield ""


def _generate(my_team, my_result, results, my_game, games, standings):
    yield "# Optimal tank scenarios for the {}".format(my_team.fullname)
    yield from _generate_tank_section(my_result, results, "Last night's tank", "Game|Score|Yay?", _generate_result_line)
    yield "---"
    yield from _generate_standings(standings)
    yield "---"
    yield from _generate_tank_section(my_game, games, "Tonight's tank", "Game|Cheer for?|Time", _generate_game_line)
    yield "---"
    yield "I'm a robot. My source is available [here](https://github.com/sbstp/tankbot)."


def generate(*args):
    return '\n'.join(_generate(*args))
