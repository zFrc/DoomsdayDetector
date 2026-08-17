import os
from datetime import datetime

from modules.services import get_sysmain_status
from modules.minecraft import get_minecraft_processes
from modules.execution import get_java_execution_events
from modules.timeline import is_within_session
from modules.doomsday import scan_doomsday
from modules.jar_analyzer import analyze_candidate
from modules.reporter import save_report


def print_line():
    print("-" * 30)


def normalize_path(path):
    if not path:
        return ""

    try:
        return os.path.normcase(
            os.path.abspath(path)
        )
    except Exception:
        return str(path).lower()


def execution_matches_candidate(event, candidate):
    candidate_path = normalize_path(
        candidate.get("path", "")
    )

    candidate_name = os.path.basename(
        candidate.get("path", "")
    ).lower()

    command_line = str(
        event.get("command_line", "")
    )

    process_path = str(
        event.get("path", "")
    )

    values = [
        command_line,
        process_path,
        str(event.get("process", "")),
    ]

    for value in values:

        if not value:
            continue

        normalized_value = normalize_path(
            value
        )

        if (
            candidate_path
            and candidate_path in normalized_value
        ):
            return True

        if (
            candidate_name
            and candidate_name in value.lower()
        ):
            return True

    return False


def find_execution_evidence(
    candidate,
    events,
    minecraft_processes
):
    executions = []

    minecraft_started = None

    if minecraft_processes:
        minecraft_started = (
            minecraft_processes[0].get(
                "started"
            )
        )

    for event in events:

        if not execution_matches_candidate(
            event,
            candidate
        ):
            continue

        within_minecraft = None

        event_time = event.get(
            "parsed_time"
        )

        if minecraft_started and event_time:
            try:
                within_minecraft = is_within_session(
                    minecraft_started,
                    event_time
                )
            except Exception:
                within_minecraft = None

        executions.append({
            "time": event.get("time"),
            "parsed_time": event_time,
            "process": event.get(
                "process",
                "Unknown"
            ),
            "pid": event.get(
                "pid",
                "Unknown"
            ),
            "minecraft": within_minecraft,
        })

    return executions


def get_execution_info(
    candidate,
    events,
    processes
):
    executions = find_execution_evidence(
        candidate,
        events,
        processes
    )

    if not executions:
        return {
            "executed": False,
            "time": None,
            "evidence": "None available",
            "minecraft": None,
        }

    executions.sort(
        key=lambda item:
        item.get("parsed_time")
        or item.get("time")
        or "",
        reverse=True
    )

    latest = executions[0]

    execution_time = latest.get(
        "parsed_time"
    )

    if execution_time:
        formatted_time = (
            execution_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    else:
        formatted_time = latest.get(
            "time"
        )

    return {
        "executed": True,
        "time": formatted_time,
        "evidence": "Windows Security 4688",
        "minecraft": latest.get(
            "minecraft"
        ),
    }


def print_execution_info(info):

    print("Execution")

    if info["executed"]:
        print("Status: CONFIRMED")

        if info["time"]:
            print(
                f"Execution time: "
                f"{info['time']}"
            )
        else:
            print(
                "Execution time: UNKNOWN"
            )

        print(
            f"Evidence: "
            f"{info['evidence']}"
        )

        if info["minecraft"] is True:
            print(
                "Minecraft session: YES"
            )

        elif info["minecraft"] is False:
            print(
                "Minecraft session: NO"
            )

        else:
            print(
                "Minecraft session: UNKNOWN"
            )

    else:
        print(
            "Status: NO EVIDENCE"
        )

        print(
            "Execution time: UNKNOWN"
        )

        print(
            "Evidence: None available"
        )

        print(
            "Minecraft session: UNKNOWN"
        )


def build_report(
    scan_time,
    scanned,
    candidates,
    confirmed,
    suspicious
):
    lines = []

    lines.append(
        "Doomsday Detector"
    )

    lines.append(
        "made by zFrc"
    )

    lines.append(
        "-" * 30
    )

    lines.append(
        f"Scan time: {scan_time}"
    )

    lines.append("")

    lines.append("Summary")
    lines.append(
        f"Files inspected: {scanned}"
    )
    lines.append(
        f"Candidates: {len(candidates)}"
    )
    lines.append(
        f"Confirmed: {len(confirmed)}"
    )
    lines.append(
        f"Suspicious: {len(suspicious)}"
    )

    lines.append("")
    lines.append("=" * 45)
    lines.append("CONFIRMED")
    lines.append("=" * 45)

    if not confirmed:
        lines.append(
            "No confirmed matches."
        )

    for item in confirmed:

        candidate = item["candidate"]
        analysis = item["analysis"]
        execution = item["execution"]

        lines.append("")
        lines.append(
            f"Name: {candidate.get('name', 'Unknown')}"
        )
        lines.append(
            f"Path: {candidate.get('path', 'Unknown')}"
        )
        lines.append(
            f"Size: {candidate.get('size', 0)} bytes"
        )
        lines.append(
            f"SHA-256: "
            f"{analysis.get('sha256', 'Unknown')}"
        )
        lines.append(
            "Status: CONFIRMED"
        )

        if execution["executed"]:
            lines.append(
                "Executed: YES"
            )
        else:
            lines.append(
                "Executed: NO EVIDENCE"
            )

        lines.append(
            "Execution time: "
            + str(
                execution["time"]
                or "UNKNOWN"
            )
        )

        lines.append(
            f"Evidence: "
            f"{execution['evidence']}"
        )

    lines.append("")
    lines.append("=" * 45)
    lines.append("SUSPICIOUS")
    lines.append("=" * 45)

    if not suspicious:
        lines.append(
            "No suspicious candidates."
        )

    for item in suspicious:

        candidate = item["candidate"]
        analysis = item["analysis"]
        execution = item["execution"]

        lines.append("")
        lines.append(
            f"Name: {candidate.get('name', 'Unknown')}"
        )
        lines.append(
            f"Path: {candidate.get('path', 'Unknown')}"
        )
        lines.append(
            f"Size: {candidate.get('size', 0)} bytes"
        )
        lines.append(
            f"Score: {analysis.get('score', 0)}"
        )
        lines.append(
            "Status: SUSPICIOUS"
        )

        if execution["executed"]:
            lines.append(
                "Executed: YES"
            )
        else:
            lines.append(
                "Executed: NO EVIDENCE"
            )

        lines.append(
            "Execution time: "
            + str(
                execution["time"]
                or "UNKNOWN"
            )
        )

        lines.append(
            f"Evidence: "
            f"{execution['evidence']}"
        )

        indicators = analysis.get(
            "indicators",
            []
        )

        if indicators:
            lines.append("Indicators:")

            for indicator in indicators:
                lines.append(
                    f"  - {indicator}"
                )

    lines.append("")
    lines.append("=" * 45)
    lines.append(
        "Scan finished."
    )

    return "\n".join(lines)


def main():

    scan_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    report_confirmed = []
    report_suspicious = []

    print()
    print("Doomsday Detector")
    print("made by zFrc")
    print_line()

    # ==========================================
    # SYSTEM
    # ==========================================

    print()
    print("System")

    try:
        sysmain = get_sysmain_status()

        print(
            f"SysMain: "
            f"{sysmain.get('status', 'UNKNOWN')}"
        )

        print(
            f"Startup: "
            f"{sysmain.get('start_type', 'UNKNOWN')}"
        )

        if sysmain.get("status") == "RUNNING":
            print(
                "Prefetch: available"
            )

        elif sysmain.get("status") == "STOPPED":
            print(
                "Prefetch: may be incomplete"
            )

        else:
            print(
                "Prefetch: unknown"
            )

    except Exception as error:

        print(
            f"SysMain: ERROR ({error})"
        )

    # ==========================================
    # MINECRAFT
    # ==========================================

    print()
    print("Minecraft")

    try:
        processes = get_minecraft_processes()
    except Exception:
        processes = []

    if not processes:

        print(
            "Minecraft: not running"
        )

    else:

        for process in processes:

            print(
                f"Client: "
                f"{process.get('client', 'Unknown')}"
            )

            print(
                f"Process: "
                f"{process.get('name', 'Unknown')}"
            )

            print(
                f"PID: "
                f"{process.get('pid', 'Unknown')}"
            )

            print(
                f"Started: "
                f"{process.get('started', 'Unknown')}"
            )

            print(
                f"Path: "
                f"{process.get('path', 'Unknown')}"
            )

            print()

    # ==========================================
    # EXECUTION HISTORY
    # ==========================================

    try:
        events = get_java_execution_events()
    except Exception:
        events = []

    # ==========================================
    # DOOMSDAY SCAN
    # ==========================================

    print()
    print("Doomsday")
    print("Scan mode: QUICK")
    print(
        "Searching common user locations..."
    )
    print()

    try:
        scan = scan_doomsday()

    except Exception as error:

        print(
            f"Scan error: {error}"
        )

        return

    candidates = scan.get(
        "candidates",
        []
    )

    scanned = scan.get(
        "scanned",
        0
    )

    print(
        f"Files inspected: {scanned}"
    )

    print(
        f"Structural candidates: "
        f"{len(candidates)}"
    )

    confirmed = []
    suspicious = []

    # ==========================================
    # ANALYSIS
    # ==========================================

    for candidate in candidates:

        try:
            analysis = analyze_candidate(
                candidate["path"]
            )
        except Exception:
            continue

        if not analysis.get("valid"):
            continue

        execution = get_execution_info(
            candidate,
            events,
            processes
        )

        item = {
            "candidate": candidate,
            "analysis": analysis,
            "execution": execution,
        }

        verdict = analysis.get(
            "verdict",
            "UNKNOWN"
        )

        if verdict == "DOOMSDAY":
            confirmed.append(item)

        elif verdict == "SUSPICIOUS":
            suspicious.append(item)

    # ==========================================
    # CONFIRMED OUTPUT
    # ==========================================

    print()

    print(
        f"Doomsday: "
        f"{len(confirmed)} CONFIRMED"
    )

    for item in confirmed:

        candidate = item["candidate"]
        analysis = item["analysis"]
        execution = item["execution"]

        print()
        print_line()

        print(
            f"Name: "
            f"{candidate.get('name', 'Unknown')}"
        )

        print(
            f"Path: "
            f"{candidate.get('path', 'Unknown')}"
        )

        print(
            f"Size: "
            f"{candidate.get('size', 0)} bytes"
        )

        print(
            f"SHA-256: "
            f"{analysis.get('sha256', 'Unknown')}"
        )

        print(
            "Status: CONFIRMED"
        )

        if execution["executed"]:
            print(
                "Executed: YES"
            )
        else:
            print(
                "Executed: NO EVIDENCE"
            )

        print(
            "Execution time: "
            + str(
                execution["time"]
                or "UNKNOWN"
            )
        )

        print(
            f"Evidence: "
            f"{execution['evidence']}"
        )

        if execution["minecraft"] is True:
            print(
                "Minecraft session: YES"
            )

        elif execution["minecraft"] is False:
            print(
                "Minecraft session: NO"
            )

        else:
            print(
                "Minecraft session: UNKNOWN"
            )

        indicators = analysis.get(
            "indicators",
            []
        )

        if indicators:

            print("Indicators:")

            for indicator in indicators:
                print(
                    f"  [+] {indicator}"
                )

        print_line()

    # ==========================================
    # SUSPICIOUS OUTPUT
    # ==========================================

    print()

    print(
        f"Suspicious candidates: "
        f"{len(suspicious)}"
    )

    suspicious.sort(
        key=lambda item:
        item["analysis"].get(
            "score",
            0
        ),
        reverse=True
    )

    for item in suspicious[:20]:

        candidate = item["candidate"]
        analysis = item["analysis"]
        execution = item["execution"]

        print()
        print_line()

        print(
            f"Name: "
            f"{candidate.get('name', 'Unknown')}"
        )

        print(
            f"Path: "
            f"{candidate.get('path', 'Unknown')}"
        )

        print(
            f"Size: "
            f"{candidate.get('size', 0)} bytes"
        )

        print(
            f"Score: "
            f"{analysis.get('score', 0)}"
        )

        print(
            "Status: SUSPICIOUS"
        )

        if execution["executed"]:
            print(
                "Executed: YES"
            )
        else:
            print(
                "Executed: NO EVIDENCE"
            )

        print(
            "Execution time: "
            + str(
                execution["time"]
                or "UNKNOWN"
            )
        )

        print(
            f"Evidence: "
            f"{execution['evidence']}"
        )

        if execution["minecraft"] is True:
            print(
                "Minecraft session: YES"
            )

        elif execution["minecraft"] is False:
            print(
                "Minecraft session: NO"
            )

        else:
            print(
                "Minecraft session: UNKNOWN"
            )

        indicators = analysis.get(
            "indicators",
            []
        )

        if indicators:

            print("Indicators:")

            for indicator in indicators:
                print(
                    f"  [!] {indicator}"
                )

        print_line()

    # ==========================================
    # SUMMARY
    # ==========================================

    print()
    print("Summary")

    print(
        f"Files inspected: {scanned}"
    )

    print(
        f"Candidates: "
        f"{len(candidates)}"
    )

    print(
        f"Confirmed: "
        f"{len(confirmed)}"
    )

    print(
        f"Suspicious: "
        f"{len(suspicious)}"
    )

    # ==========================================
    # REPORT
    # ==========================================

    report_content = build_report(
        scan_time,
        scanned,
        candidates,
        confirmed,
        suspicious
    )

    report_path = save_report(
        report_content
    )

    print()

    if report_path:

        print(
            f"Report saved: "
            f"{report_path}"
        )

    else:

        print(
            "Report: unable to save"
        )

    print()
    print_line()
    print("Scan finished.")


if __name__ == "__main__":
    main()