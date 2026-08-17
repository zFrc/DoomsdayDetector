from datetime import datetime


def parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).astimezone()
    except (ValueError, TypeError):
        return None


def is_within_session(started, execution_time):
    minecraft_time = parse_time(started)
    execution = parse_time(execution_time)

    if not minecraft_time or not execution:
        return None

    return execution >= minecraft_time