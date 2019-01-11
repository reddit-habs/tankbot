from enum import Enum

from attr import attrib, attrs


class BaseMatchup:
    def get_cheer(self):
        raise NotADirectoryError

    def get_mood(self):
        raise NotImplementedError


class Mood(Enum):
    WORST = 0
    BAD = 1
    NEUTRAL = 2
    GOOD = 3
    GREAT = 4
    NOT_RELEVANT = 5

    def __str__(self):
        d = {
            Mood.WORST: "Worst",
            Mood.BAD: "Bad",
            Mood.NEUTRAL: "Neutral",
            Mood.GOOD: "Good",
            Mood.GREAT: "Great",
            Mood.NOT_RELEVANT: "Not relevant",
        }
        return d.get(self)


@attrs
class Cheer:
    team = attrib()
    overtime = attrib()
