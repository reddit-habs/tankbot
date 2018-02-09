import json

import arrow
import requests
from attr import attrs, attrib
from fake_useragent import UserAgent
from requests import Request, Session


@attrs(slots=True, hash=True)
class Team:
    id = attrib()
    code = attrib(cmp=False)
    fullname = attrib(cmp=False)
    name = attrib(cmp=False)
    location = attrib(cmp=False)
    standing = attrib(cmp=False, init=False, repr=False)


@attrs(slots=True)
class Standing:
    team = attrib()
    place = attrib()
    gamesPlayed = attrib()
    points = attrib()
    wins = attrib()
    losses = attrib()
    ot = attrib()
    row = attrib()


@attrs(slots=True)
class Game:
    time = attrib()
    home = attrib()
    away = attrib()


@attrs(slots=True)
class Result(Game):
    home_score = attrib()
    away_score = attrib()
    winner = attrib(init=False)

    def __attrs_post_init__(self):
        self.winner = self.home if self.home_score > self.away_score else self.away


class Info:

    def __init__(self):
        self._ua = UserAgent()
        self.teams = []
        self.standings = []
        self.games = []
        self.results = []

        self._team_id_map = {}
        self._team_code_map = {}
        self._standing_team_map = {}

        self._get_teams()
        self._get_standings()
        self._get_games()
        self._get_results()

    def get_team_by_id(self, id):
        return self._team_id_map[id]

    def get_team_by_code(self, code):
        return self._team_code_map[code.lower()]

    def get_standing(self, team):
        return self._standing_team_map[team]

    def _fetch_json(self, url, params=None):
        headers = {
            'User-Agent': self._ua.random,
        }
        resp = requests.get(url, params=params, headers=headers)
        return resp.json()

    def _get_teams(self):
        data = self._fetch_json("https://statsapi.web.nhl.com/api/v1/teams")
        for entry in data['teams']:
            team = Team(id=entry['id'],
                        code=entry['abbreviation'],
                        fullname=entry['name'],
                        location=entry['locationName'],
                        name=entry['teamName'])
            self.teams.append(team)
            self._team_id_map[team.id] = team
            self._team_code_map[team.code.lower()] = team

    def _get_standings(self):
        data = self._fetch_json("https://statsapi.web.nhl.com/api/v1/standings/byLeague")
        place = 1
        for entry in data['records'][0]['teamRecords']:
            team = self.get_team_by_id(entry['team']['id'])
            standing = Standing(team=team,
                                place=place,
                                gamesPlayed=entry['gamesPlayed'],
                                points=entry['points'],
                                wins=entry['leagueRecord']['wins'],
                                losses=entry['leagueRecord']['losses'],
                                ot=entry['leagueRecord']['ot'],
                                row=entry['row'])
            self.standings.append(standing)
            self._standing_team_map[team] = standing
            team.standing = standing
            place += 1

    def _get_games(self):
        today = arrow.now().date().isoformat()
        data = self._fetch_json("https://statsapi.web.nhl.com/api/v1/schedule",
                                params=dict(startDate=today, endDate=today))
        for entry in data['dates'][0]['games']:
            date = arrow.get(entry['gameDate']).to('local')
            home = self.get_team_by_id(entry['teams']['home']['team']['id'])
            away = self.get_team_by_id(entry['teams']['away']['team']['id'])
            game = Game(time=date, home=home, away=away)
            self.games.append(game)

    def _get_results(self):
        yeserday = arrow.now().shift(days=-1).date().isoformat()
        data = self._fetch_json("https://statsapi.web.nhl.com/api/v1/schedule",
                                params=dict(startDate=yeserday, endDate=yeserday))
        for entry in data['dates'][0]['games']:
            date = arrow.get(entry['gameDate']).to('local')
            home = self.get_team_by_id(entry['teams']['home']['team']['id'])
            away = self.get_team_by_id(entry['teams']['away']['team']['id'])
            result = Result(time=date, home=home, away=away,
                            home_score=entry['teams']['home']['score'], away_score=entry['teams']['away']['score'])
            self.results.append(result)


class CachedInfo(Info):

    def __init__(self):
        self._session = Session()
        self._cache = {}
        self._load()
        Info.__init__(self)

    def _load(self):
        try:
            with open('request_cache.json') as f:
                self._cache = json.load(f)
        except FileNotFoundError:
            pass

    def _save(self):
        with open('request_cache.json', 'w') as f:
            json.dump(self._cache, f)

    def _fetch_json(self, url, params=None):
        req = Request('GET', url, params=params)
        prep = req.prepare()
        entry = self._cache.get(prep.url)
        if entry is not None:
            return entry
        else:
            res = self._session.send(prep)
            data = res.json()
            self._cache[res.url] = data
            self._save()
            return data
