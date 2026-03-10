from datetime import timedelta


def milliseconds(duration: timedelta) -> int:
    """Return the duration converted to whole milliseconds."""
    return int(duration.total_seconds() * 1000)
