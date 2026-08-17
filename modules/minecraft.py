import subprocess
import json
from datetime import datetime, timezone


def parse_wmi_date(value):
    if not value:
        return None

    try:
        timestamp = int(value.strip("/Date()"))
        return datetime.fromtimestamp(timestamp / 1000, timezone.utc).astimezone()
    except (ValueError, TypeError):
        return None


def get_minecraft_processes():
    processes = []

    command = """
    Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match 'java|javaw|Minecraft'
    } |
    Select-Object Name, ProcessId, ExecutablePath, CommandLine, CreationDate |
    ConvertTo-Json -Compress
    """

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if not result.stdout.strip():
            return processes

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        for process in data:
            name = process.get("Name") or ""
            path = process.get("ExecutablePath") or ""
            command_line = process.get("CommandLine") or ""

            lower_path = path.lower()
            lower_command = command_line.lower()

            is_lunar = (
                ".lunarclient" in lower_path
                or "lunar" in lower_command
                or "moonsworth" in lower_command
            )

            is_minecraft = (
                "minecraft" in lower_command
                or "net.minecraft" in lower_command
                or "moonsworth" in lower_command
            )

            if not (is_lunar or is_minecraft):
                continue

            started = parse_wmi_date(process.get("CreationDate"))

            processes.append({
                "name": name,
                "pid": process.get("ProcessId"),
                "path": path,
                "started": started.strftime("%Y-%m-%d %H:%M:%S")
                if started else "UNKNOWN",
                "client": "Lunar Client" if is_lunar else "Minecraft"
            })

    except Exception as error:
        print(f"Could not read Minecraft process: {error}")

    return processes