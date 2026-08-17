from datetime import datetime
from pathlib import Path


def create_report_directory():
    directory = Path("reports")
    directory.mkdir(
        parents=True,
        exist_ok=True
    )
    return directory


def create_report_file():
    directory = create_report_directory()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    return directory / (
        f"scan_{timestamp}.txt"
    )


def save_report(content):
    path = create_report_file()

    try:
        path.write_text(
            content,
            encoding="utf-8"
        )

        return str(path)

    except OSError:
        return None