from setuptools import setup

setup(
    name="tankbot",
    version="0.0.1",
    packages=['tankbot'],
    install_requires=['arrow', 'attrs', 'fake_useragent', 'praw', 'requests'],
)
