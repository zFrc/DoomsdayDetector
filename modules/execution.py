import subprocess
import json
from datetime import datetime


def parse_event_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).astimezone()

    except (ValueError, TypeError):
        return None


def get_java_execution_events():
    events = []

    query = r"""
    Get-WinEvent -FilterHashtable @{
        LogName='Security'
        Id=4688
    } -MaxEvents 500 -ErrorAction SilentlyContinue |
    ForEach-Object {

        $xml = [xml]$_.ToXml()
        $data = @{}

        foreach ($item in $xml.Event.EventData.Data) {
            $data[$item.Name] = $item.'#text'
        }

        [PSCustomObject]@{
            TimeCreated = $_.TimeCreated.ToString("o")
            NewProcessName = $data["NewProcessName"]
            NewProcessId = $data["NewProcessId"]
            CreatorProcessName = $data["CreatorProcessName"]
            CommandLine = $data["CommandLine"]
        }

    } |
    ConvertTo-Json -Compress
    """

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                query
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )

        if not result.stdout.strip():
            return events

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        for event in data:

            process_path = (
                event.get("NewProcessName")
                or ""
            )

            process_name = (
                process_path
                .replace("/", "\\")
                .split("\\")[-1]
                .lower()
            )

            if process_name not in (
                "java.exe",
                "javaw.exe"
            ):
                continue

            raw_time = event.get(
                "TimeCreated"
            )

            parsed_time = parse_event_time(
                raw_time
            )

            command_line = (
                event.get("CommandLine")
                or ""
            )

            command_lower = command_line.lower()

            jar_execution = (
                "-jar" in command_lower
            )

            events.append({
                "time": raw_time,

                "parsed_time": parsed_time,

                "process": process_name,

                "pid": event.get(
                    "NewProcessId"
                ),

                "parent": (
                    event.get(
                        "CreatorProcessName"
                    )
                    or ""
                )
                .replace("/", "\\")
                .split("\\")[-1]
                .lower(),

                "path": process_path,

                "jar_execution": jar_execution,

                "command_line_present": bool(
                    command_line.strip()
                ),

                # Se mantiene solamente para que otros
                # módulos puedan hacer una comparación.
                # Nunca debemos imprimirlo.
                "command_line": command_line,
            })

    except subprocess.TimeoutExpired:
        return events

    except (
        json.JSONDecodeError,
        OSError,
        ValueError
    ):
        return events

    except Exception:
        return events

    return events