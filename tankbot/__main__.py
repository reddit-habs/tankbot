from pprint import pprint

from . import date
from .api import Info


if __name__ == '__main__':
    x = Info()
    pprint(x.teams)
    pprint(x.standings)
    pprint(x.games)
    pprint(x.results)
