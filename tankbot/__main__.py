import argparse
import json

import arrow
import praw

from .analysis import Analysis
from .api import CachedInfo, Info
from .generate import generate


def date(s):
    try:
        return arrow.get(s, 'YYYY-MM-DD')
    except arrow.parser.ParserError:
        raise ValueError("invalid date")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='tankbot')
    parser.add_argument('--date', default=None, help="date to analyse, YYYY-MM-DD format", type=date)
    args = parser.parse_args()

    with open('config.json') as f:
        config = json.load(f)
        test = config.get("test", False)

        info = CachedInfo(args.date) if test else Info(args.date)
        my_team = info.get_team_by_code(config['my_team'])
        analysis = Analysis(info, my_team)

        text = generate(analysis)

        if test:
            print(text)
        else:
            reddit = praw.Reddit(client_id=config['client_id'],
                                 client_secret=config['client_secret'],
                                 username=config['username'],
                                 password=config['password'],
                                 user_agent=config['user_agent'])

            sub = reddit.subreddit(config['subreddit'])
            title = "Scouting the Tank: {}".format(info.date.format('MMMM Do, YYYY'))
            sub.submit(title, selftext=text)
