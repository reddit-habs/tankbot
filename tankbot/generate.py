def _underline_header(header):
    return "|".join(["---"] * len(header.split('|')))


def _generate_result_line(r):
    yield "{} at {}|{}-{} {}|{}".format(
        r.game.away.code.upper(),
        r.game.home.code.upper(),
        r.game.away_score,
        r.game.home_score,
        r.game.winner.code.upper(),
        "YES" if r.game.winner == r.tanker else "NO",
    )


def _generate_game_line(r):
    yield "{} at {}|{}|{}".format(
        r.game.away.code.upper(),
        r.game.home.code.upper(),
        "OVERTIME" if r.overtime else r.tanker.code.upper(),
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
        yield "{}|{}|{}|{}|{}|{}".format(
            s.place,
            s.team.code.upper(),
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
        yield "No tank tonight."
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


def generate(my_result, results, my_game, games, standings):
    yield from _generate_tank_section(my_result, results, "Last night's tank", "Game|Score|Yay?", _generate_result_line)
    yield "---"
    yield from _generate_standings(standings)
    yield "---"
    yield from _generate_tank_section(my_game, games, "Tonight's tank", "Game|Cheer for?|Time", _generate_game_line)
