import argparse
import json
import sys

import arrow
import praw
import tankbot.analysis.playoffs
import tankbot.analysis.tank
import tankbot.generate.playoffs
import tankbot.generate.tank
from tankbot.api import fetch_info


def date(s):
    try:
        return arrow.get(s, "YYYY-MM-DD")
    except arrow.parser.ParserError:
        raise ValueError("invalid date")


def write_or_post(test, reddit, my_team, title, text):
    if test:
        with open("{}.md".format(my_team.code), "w") as f:
            f.write(text)
    else:
        try:
            sub = reddit.subreddit(my_team.subreddit)
            sub.submit(title, selftext=text, send_replies=False)
        except Exception as e:
            print("Error sending", e, file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="tankbot")
    parser.add_argument("--date", default=None, help="date to analyse, YYYY-MM-DD format", type=date)
    args = parser.parse_args()

    with open("config.json") as f:
        config = json.load(f)
        test = config.get("test", False)

        info = fetch_info(args.date)

        # from tankbot import serde
        # serde.dumpf("info2.json", info, indent=4)

        reddit = None

        if not test:
            reddit = praw.Reddit(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                username=config["username"],
                password=config["password"],
                user_agent=config["user_agent"],
            )

        for team in config["playoffs"]:
            my_team = info.get_team_by_code(team)
            a = tankbot.analysis.playoffs.Analysis(info, my_team)
            text = tankbot.generate.playoffs.generate(a)
            title = "Playoffs Race: {}".format(info.date.format("MMMM Do, YYYY"))
            write_or_post(test, reddit, my_team, title, text)
        for team in config["tank"]:
            my_team = info.get_team_by_code(team)
            a = tankbot.analysis.tank.Analysis(info, my_team)
            text = tankbot.generate.tank.generate(a)
            title = "Scouting the Tank: {}".format(info.date.format("MMMM Do, YYYY"))
            write_or_post(test, reddit, my_team, title, text)
