from attr import attrib, attrs

import arrow
import nhlapi.io
from nhlapi.endpoints import NHLAPI

from . import localdata
from .util import f


def _format_record(wins, losses, ot):
    # return f"{wins}-{losses}-{ot}"
    return f("{}-{}-{}", wins, losses, ot)


@attrs(slots=True, hash=True)
class Team:
    id = attrib()
    code = attrib(cmp=False)
    fullname = attrib(cmp=False)
    name = attrib(cmp=False)
    location = attrib(cmp=False)
    division = attrib(cmp=False)
    conference = attrib(cmp=False)
    subreddit = attrib(cmp=False, default=None)


@attrs(slots=True, cmp=False)
class Standing:
    team = attrib()
    place = attrib()
    gamesPlayed = attrib()
    points = attrib()
    wins = attrib()
    losses = attrib()
    ot = attrib()
    record = attrib(init=False)
    row = attrib()
    last10 = attrib()
    projection = attrib(init=False)
    point_percent = attrib(init=False)
    odds = attrib(init=False)
    seed = attrib(default=None)

    def __attrs_post_init__(self):
        self.record = _format_record(self.wins, self.losses, self.ot)
        self.projection = round((self.points / self.gamesPlayed) * 82)
        self.point_percent = f("{self.points / (self.gamesPlayed * 2):0.3f}")


@attrs(slots=True)
class Game:
    time = attrib()
    home = attrib()
    away = attrib()


@attrs(slots=True)
class Result(Game):
    home_score = attrib()
    away_score = attrib()
    overtime = attrib()
    winner = attrib(init=False)

    def __attrs_post_init__(self):
        self.winner = self.home if self.home_score > self.away_score else self.away


@attrs(slots=True)
class Info:
    teams = attrib()
    date = attrib(default=None)
    standings = attrib(factory=list)
    past_standings = attrib(factory=list)
    games = attrib(factory=list)
    results = attrib(factory=list)
    past_date = attrib(init=False)

    _team_id_map = attrib(init=False, factory=dict)
    _team_code_map = attrib(init=False, factory=dict)
    _standings_team_map = attrib(init=False, factory=dict)
    _past_standings_team_map = attrib(init=False, factory=dict)

    def __attrs_post_init__(self):
        if self.date is None:
            self.date = arrow.now()
        self.past_date = self.date.shift(days=-1)
        self._rebuild_cache()

    def _rebuild_cache(self):
        for team in self.teams:
            self._team_id_map[team.id] = team
            self._team_code_map[team.code.lower()] = team
        self._map_standings(self._standings_team_map, self.standings)
        self._map_standings(self._past_standings_team_map, self.past_standings)

    def _map_standings(self, smap, standings):
        for s in standings:
            smap[s.team] = s

    def get_team_by_id(self, id):
        return self._team_id_map[id]

    def get_team_by_code(self, code):
        return self._team_code_map[code.lower()]

    def get_standing(self, team, past=False):
        if past:
            return self._past_standings_team_map[team]
        return self._standings_team_map[team]


def _get_teams(client):
    teams = []
    data = client.teams()
    for entry in data.teams:
        team = Team(
            id=entry.id,
            code=entry.abbreviation,
            fullname=entry.name,
            location=entry.locationName,
            name=entry.teamName,
            division=entry.division.name,
            conference=entry.conference.name,
        )
        teams.append(team)

    # add subreddits
    teams = list(sorted(teams, key=lambda t: t.fullname))
    for idx, team in enumerate(teams):
        team.subreddit = localdata.subreddits[idx]

    return teams


def _get_last10(entry):
    filtered = [r for r in entry["records"]["overallRecords"] if r["type"] == "lastTen"]
    if len(filtered) > 0:
        rec = filtered[0]
        return _format_record(rec["wins"], rec["losses"], rec["ot"])
    else:
        return "N/A"


def _get_standings(info, client, date, past=False):
    data = client.standings(expand="standings.record")
    standings = info.past_standings if past else info.standings
    place = 1
    for entry in data.records[0].teamRecords:
        team = info.get_team_by_id(entry.team.id)
        standing = Standing(
            team=team,
            place=place,
            gamesPlayed=entry.gamesPlayed,
            points=entry.points,
            wins=entry.leagueRecord.wins,
            losses=entry.leagueRecord.losses,
            ot=entry.leagueRecord.ot,
            row=entry.row,
            last10=_get_last10(entry),
        )
        standings.append(standing)
        place += 1

    for s in standings:
        try:
            s.odds = localdata.lottery[len(info.teams) - s.place]
        except IndexError:
            s.odds = 0


def _get_games(info, client):
    today = info.date.date().isoformat()
    data = client.schedule(start_date=today, end_date=today)
    for entry in data.dates[0].games:
        date = arrow.get(entry.gameDate).to("local")
        home = info.get_team_by_id(entry.teams.home.team.id)
        away = info.get_team_by_id(entry.teams.away.team.id)
        game = Game(time=date, home=home, away=away)
        info.games.append(game)


def _get_results(info, client):
    yesterday = info.past_date.date().isoformat()
    data = client.schedule(start_date=yesterday, end_date=yesterday, expand="schedule.linescore")
    for entry in data.dates[0].games:
        date = arrow.get(entry.gameDate).to("local")
        home = info.get_team_by_id(entry.teams.home.team.id)
        away = info.get_team_by_id(entry.teams.away.team.id)
        result = Result(
            time=date,
            home=home,
            away=away,
            home_score=entry.teams.home.score,
            away_score=entry.teams.away.score,
            overtime=len(entry.linescore.periods) > 3,
        )
        info.results.append(result)


def fetch_info(date=None):
    client = NHLAPI(nhlapi.io.Client())

    info = Info(_get_teams(client), date)
    _get_standings(info, client, info.date)
    _get_standings(info, client, info.past_date, True)
    _get_games(info, client)
    _get_results(info, client)
    info._rebuild_cache()

    return info
