import argparse
import json
import sys

import arrow
import praw

from .analysis.tank import Analysis
from .api import Info
from .generate.tank import generate


def date(s):
    try:
        return arrow.get(s, "YYYY-MM-DD")
    except arrow.parser.ParserError:
        raise ValueError("invalid date")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="tankbot")
    parser.add_argument("--date", default=None, help="date to analyse, YYYY-MM-DD format", type=date)
    args = parser.parse_args()

    with open("config.json") as f:
        config = json.load(f)
        test = config.get("test", False)

        info = Info(args.date)

        if not test:
            reddit = praw.Reddit(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                username=config["username"],
                password=config["password"],
                user_agent=config["user_agent"],
            )

        for team in config["teams"]:
            my_team = info.get_team_by_code(team)
            analysis = Analysis(info, my_team)

            text = generate(analysis)

            if test:
                with open("{}.md".format(my_team.code), "w") as f:
                    f.write(text)
            else:
                try:
                    sub = reddit.subreddit(my_team.subreddit)
                    title = "Scouting the Tank: {}".format(info.date.format("MMMM Do, YYYY"))
                    sub.submit(title, selftext=text, send_replies=False)
                except Exception as e:
                    print("Error sending", e, file=sys.stderr)
