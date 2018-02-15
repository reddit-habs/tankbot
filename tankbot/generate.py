from .analysis import Analysis
from .markdown import Document, List, H1, H2, Paragraph, Table


def fmt_team(team):
    return f"[](/r/{team.subreddit}) {team.code.upper()}"


def fmt_vs(away, home):
    return f"{fmt_team(away)} at {fmt_team(home)}"


def get_mood(a: Analysis, r):
    # TODO cleanup this mess
    # if the team is my team, we want to lose
    if r.tanker == a.my_team:
        # our team won, bad
        if r.game.winner == a.my_team:
            return "No"
        # game went to overtime, meh
        elif r.game.overtime:
            return "Half yay"
        # no points for us, perfect
        else:
            return "Yes"
    # if the tanker isn't my team, we want him to win
    else:
        # if should have went to overtime and it did, perfect
        if r.overtime and r.game.overtime:
            return "Perfect"
        # if the enemy tanker won
        elif r.tanker == r.game.winner:
            return "Yes"
        # if the enemy tanker didn't win but went to OT
        elif r.game.overtime:
            return "Half yay"
        # no win, no OT
        else:
            return "No"


def get_cheer(a: Analysis, m):
    if m.tanker == a.my_team:
        if m.tanker == m.game.away:
            team = m.game.home
        else:
            team = m.game.away
    else:
        team = m.tanker
    if m.overtime:
        return f"{fmt_team(team)} (OT)"
    else:
        return fmt_team(team)


def make_result_table(a: Analysis, results):
    t = Table()
    t.add_columns("Game", "Score", "Yay?")

    for r in results:
        ot = "(OT)" if r.game.overtime else ""
        t.add_row(
            fmt_vs(r.game.away, r.game.home),
            f"{r.game.away_score}-{r.game.home_score} {fmt_team(r.game.winner)} {ot}",
            get_mood(a, r),
        )

    return t


def make_standings_table(a: Analysis):
    t = Table()
    t.add_columns("Place", "Team", "GP", "Record", "Points", "ROW", "L10", "1st OA odds")
    for s in a.standings:
        t.add_row(
            s.place,
            fmt_team(s.team),
            s.gamesPlayed,
            s.record,
            s.points,
            s.row,
            s.last10,
            s.odds,
        )
    return t


def make_games_table(a: Analysis, games):
    t = Table()
    t.add_columns("Game", "Cheer for?", "Time")
    for g in games:
        t.add_row(
            fmt_vs(g.game.away, g.game.home),
            get_cheer(a, g),
            g.time,
        )
    return t


def generate(a: Analysis):
    doc = Document()
    doc.add(H1("Scouting the Tank"))

    # results

    # own result
    doc.add(H2("Last night's tank"))
    doc.add(List(["De Tanque:"]))
    if a.my_result:
        t = make_result_table(a, [a.my_result])
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing."))

    # out of town results
    doc.add(List(["Out of town tank:"]))
    if len(a.results) > 0:
        t = make_result_table(a, a.results)
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing out of town."))

    # standings
    doc.add(H2("Standings"))
    doc.add(make_standings_table(a))
    doc.add(
        Paragraph("[Lottery odds, as well as a Lottery Simulator can be found here.](http://nhllotterysimulator.com)")
    )

    # games

    # own game
    doc.add(H2("Tonight's tank"))
    doc.add(List(["De Tanque:"]))
    if a.my_game:
        t = make_games_table(a, [a.my_game])
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing."))

    # out of town games
    doc.add(List(["Out of town tank:"]))
    if len(a.games) > 0:
        t = make_games_table(a, a.games)
        doc.add(t)
    else:
        doc.add(Paragraph("Nothing out of town."))

    return doc.render()
