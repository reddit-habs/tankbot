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
    subreddit = attrib(init=False)


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
    odds = attrib(init=False)

    def __attrs_post_init__(self):
        self.record = _format_record(self.wins, self.losses, self.ot)
        self.projection = round((self.points / self.gamesPlayed) * 82)


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


class Info:
    def __init__(self, date=None):
        if date is None:
            date = arrow.now()
        self.date = date
        self.past_date = date.shift(days=-1)
        self.teams = []
        self.games = []
        self.results = []

        self._team_id_map = {}
        self._team_code_map = {}
        self._standings_team_map = {}
        self._past_standings_team_map = {}
        self._client = NHLAPI(nhlapi.io.Client())

        self._get_teams()

        self.standings = self._get_standings(date)
        self.past_standings = self._get_standings(self.past_date)
        self._map_standings(self._standings_team_map, self.standings)
        self._map_standings(self._past_standings_team_map, self.past_standings)

        self._get_games()
        self._get_results()

    def get_team_by_id(self, id):
        return self._team_id_map[id]

    def get_team_by_code(self, code):
        return self._team_code_map[code.lower()]

    def get_standing(self, team, past=False):
        if past:
            return self._past_standings_team_map[team]
        return self._standings_team_map[team]

    def _get_teams(self):
        data = self._client.teams()
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
            self.teams.append(team)
            self._team_id_map[team.id] = team
            self._team_code_map[team.code.lower()] = team
        self._load_subreddits()

    def _load_subreddits(self):
        teams = list(sorted(self.teams, key=lambda t: t.fullname))
        for idx, team in enumerate(teams):
            team.subreddit = localdata.subreddits[idx]

    def _get_last10(self, entry):
        filtered = [r for r in entry["records"]["overallRecords"] if r["type"] == "lastTen"]
        if len(filtered) > 0:
            rec = filtered[0]
            return _format_record(rec["wins"], rec["losses"], rec["ot"])
        else:
            return "N/A"

    def _get_standings(self, date):
        data = self._client.standings(expand="standings.record")
        standings = []
        place = 1
        for entry in data.records[0].teamRecords:
            team = self.get_team_by_id(entry.team.id)
            standing = Standing(
                team=team,
                place=place,
                gamesPlayed=entry.gamesPlayed,
                points=entry.points,
                wins=entry.leagueRecord.wins,
                losses=entry.leagueRecord.losses,
                ot=entry.leagueRecord.ot,
                row=entry.row,
                last10=self._get_last10(entry),
            )
            standings.append(standing)
            place += 1
        self._load_lottery_odds(standings)
        return standings

    def _load_lottery_odds(self, standings):
        for s in standings:
            try:
                s.odds = localdata.lottery[len(self.teams) - s.place]
            except IndexError:
                s.odds = 0

    def _map_standings(self, smap, standings):
        for s in standings:
            smap[s.team] = s

    def _get_games(self):
        today = self.date.date().isoformat()
        data = self._client.schedule(start_date=today, end_date=today)
        for entry in data.dates[0].games:
            date = arrow.get(entry.gameDate).to("local")
            home = self.get_team_by_id(entry.teams.home.team.id)
            away = self.get_team_by_id(entry.teams.away.team.id)
            game = Game(time=date, home=home, away=away)
            self.games.append(game)

    def _get_results(self):
        yesterday = self.past_date.date().isoformat()
        data = self._client.schedule(start_date=yesterday, end_date=yesterday, expand="schedule.linescore")
        for entry in data.dates[0].games:
            date = arrow.get(entry.gameDate).to("local")
            home = self.get_team_by_id(entry.teams.home.team.id)
            away = self.get_team_by_id(entry.teams.away.team.id)
            result = Result(
                time=date,
                home=home,
                away=away,
                home_score=entry.teams.home.score,
                away_score=entry.teams.away.score,
                overtime=len(entry.linescore.periods) > 3,
            )
            self.results.append(result)
