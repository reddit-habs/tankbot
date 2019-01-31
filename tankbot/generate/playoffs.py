import typing

from ..analysis.tank import Analysis, Matchup
from ..api import Standing
from ..markdown import H1, H2, Document, HorizontalRule, List, Paragraph, Table
from ..util import f


def fmt_team(team):
    # return f"[](/r/{team.subreddit}) {team.code.upper()}"
    return f("[](/r/{}) {}", team.subreddit, team.code.upper())


def fmt_vs(away, home):
    # return f"{fmt_team(away)} at {fmt_team(home)}"
    return f("{} at {}", fmt_team(away), fmt_team(home))


def fmt_seed(s: Standing):
    return f("[](/r/{s.team.subreddit}) {s.team.code.upper()} ({s.place})")


def get_cheer(a: Analysis, m: Matchup):
    cheer = m.get_cheer()
    if cheer.overtime:
        # return f"{fmt_team(team)} (OT)"
        return f("{} (OT)", fmt_team(cheer.team))
    else:
        return fmt_team(cheer.team)


def make_result_table(a: Analysis, results):
    t = Table()
    t.add_columns("Game", "Score", "Outcome")

    for r in results:
        ot = "(OT)" if r.game.overtime else ""
        t.add_row(
            fmt_vs(r.game.away, r.game.home),
            # f"{r.game.away_score}-{r.game.home_score} {fmt_team(r.game.winner)} {ot}",
            f("{}-{} {} {}", r.game.away_score, r.game.home_score, fmt_team(r.game.winner), ot),
            str(r.get_mood()),
        )

    return t


def make_standings_table(standings: typing.List[Standing]):
    t = Table()
    t.add_columns("Place", "Team", "GP", "Record", "Points", "ROW", "L10", "P%", "P-82")
    for s in standings[:3]:
        t.add_row(
            s.seed or "",
            fmt_team(s.team),
            s.gamesPlayed,
            s.record,
            s.points,
            s.row,
            s.last10,
            s.point_percent,
            s.projection,
        )
    return t


def make_wildcard_table(standings: typing.List[Standing]):
    t = Table()
    t.add_columns("Place", "Team", "GP", "Record", "Points", "ROW", "L10", "P%", "P-82")
    for i, s in enumerate(standings):
        if i == 2:
            t.add_row("-", "-", "-", "-", "-", "-", "-", "-", "-")
        t.add_row(
            s.seed or "",
            fmt_team(s.team),
            s.gamesPlayed,
            s.record,
            s.points,
            s.row,
            s.last10,
            s.point_percent,
            s.projection,
        )
    return t


def make_matchups_table(a: Analysis):
    t = Table()
    t.add_columns("High seed", "", "Low seed")
    for m in a.playoffs_matchups:
        t.add_row(fmt_seed(m.high_team), "vs", fmt_seed(m.low_team))
    return t


def make_games_table(a: Analysis, games):
    t = Table()
    t.add_columns("Game", "Cheer for", "Time")
    for g in games:
        t.add_row(fmt_vs(g.game.away, g.game.home), get_cheer(a, g), g.time)
    return t


def generate(a: Analysis):
    doc = Document()
    doc.add(H1("Race to the Playoffs"))

    # results

    # own result
    doc.add(H2("Last night's race"))
    doc.add(List(["Our race:"]))
    if a.my_result:
        t = make_result_table(a, [a.my_result])
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing."))

    # out of town results
    doc.add(List(["Outside of town:"]))
    if len(a.results) > 0:
        t = make_result_table(a, a.results)
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing out of town."))
    doc.add(HorizontalRule())

    # standings
    doc.add(H2("Standings"))
    doc.add(make_standings_table(a.own_division))
    doc.add(make_standings_table(a.other_division))
    doc.add(make_wildcard_table(a.wildcard))
    doc.add(HorizontalRule())

    # playoffs matchups
    doc.add(H2("Current playoffs matchups"))
    doc.add(make_matchups_table(a))
    doc.add(HorizontalRule())

    # games

    # own game
    doc.add(H2("Tonight's race"))
    doc.add(List(["Our race:"]))
    if a.my_game:
        t = make_games_table(a, [a.my_game])
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing."))

    # out of town games
    doc.add(List(["Out of town:"]))
    if len(a.games) > 0:
        t = make_games_table(a, a.games)
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing out of town."))

    doc.add(HorizontalRule())
    doc.add(
        Paragraph(
            """/u/AutoYouppi is an umbrella account for multiple bots.
They are FOSS and their source code is available [here](https://github.com/reddit-habs)."""
        )
    )

    return doc.render()
