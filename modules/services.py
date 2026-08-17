import subprocess


def get_sysmain_status():
    try:
        result = subprocess.run(
            ["sc", "query", "SysMain"],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace"
        )

        output = result.stdout

        state = "UNKNOWN"

        if "RUNNING" in output:
            state = "RUNNING"
        elif "STOPPED" in output:
            state = "STOPPED"

        config = subprocess.run(
            ["sc", "qc", "SysMain"],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace"
        )

        config_output = config.stdout

        start_type = "UNKNOWN"

        if "AUTO_START" in config_output:
            start_type = "AUTOMATIC"
        elif "DEMAND_START" in config_output:
            start_type = "MANUAL"
        elif "DISABLED" in config_output:
            start_type = "DISABLED"

        return {
            "status": state,
            "start_type": start_type
        }

    except Exception as error:
        return {
            "status": "ERROR",
            "start_type": "ERROR",
            "error": str(error)
        }
    