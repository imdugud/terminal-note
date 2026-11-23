from datetime import date, datetime, timedelta

DATE_FORMAT = "%d-%m-%Y"


def parse_date_arg(value, today=None):
    """Parse a --date value: 'today', 'tomorrow', or 'DD-MM-YYYY'."""
    today = today or date.today()
    if value is None or value == "today":
        return today
    if value == "tomorrow":
        return today + timedelta(days=1)
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise ValueError(
            f"Invalid date '{value}'. Use 'today', 'tomorrow', or DD-MM-YYYY."
        )


def format_date(d):
    return d.strftime(DATE_FORMAT)


def parse_stored_date(s):
    """Parse a DD-MM-YYYY date string read back from a task line."""
    return datetime.strptime(s, DATE_FORMAT).date()
