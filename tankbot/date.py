from datetime import date, timedelta


def format_date(date):
    return date.iso_format()


def today():
    return format_date(date.today())


def yesterday():
    yesterday = today() - timedelta(days=1)
    return format_date(yesterday)
