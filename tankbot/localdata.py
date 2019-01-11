_SUBREDDITS = """\
anaheimducks
coyotes
bostonbruins
sabres
calgaryflames
canes
hawks
coloradoavalanche
bluejackets
dallasstars
detroitredwings
edmontonoilers
floridapanthers
losangeleskings
wildhockey
habs
predators
devils
newyorkislanders
rangers
ottawasenators
flyers
penguins
sanjosesharks
stlouisblues
tampabaylightning
leafs
canucks
goldenknights
caps
winnipegjets
"""
subreddits = _SUBREDDITS.splitlines()

_LOTTERY = """\
18.0
12.5
10.5
9.5
8.5
7.6
6.7
5.8
5.4
4.5
3.3
2.7
2.2
1.8
1.0
"""
lottery = list(map(float, _LOTTERY.splitlines()))
