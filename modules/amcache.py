import os
import subprocess
import tempfile


def get_amcache_entries():

    results = []

    hive = os.path.expandvars(
        r"%windir%\AppCompat\Programs\Amcache.hve"
    )

    if not os.path.exists(hive):
        return results

    # Copiamos el hive a TEMP para no trabajar directamente
    # sobre el archivo del sistema.
    temp_hive = os.path.join(
        tempfile.gettempdir(),
        "DoomsdayDetector_Amcache.hve"
    )

    try:

        copy_result = subprocess.run(
            [
                "cmd",
                "/c",
                "copy",
                "/Y",
                hive,
                temp_hive
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10
        )

        if copy_result.returncode != 0:
            return results

        # Consultamos solamente información legible del hive.
        query = [
            "reg",
            "load",
            r"HKU\DoomsdayDetectorAmcache",
            temp_hive
        ]

        loaded = subprocess.run(
            query,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10
        )

        if loaded.returncode != 0:
            return results

        try:

            result = subprocess.run(
                [
                    "reg",
                    "query",
                    r"HKU\DoomsdayDetectorAmcache\Root\File",
                    "/s"
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20
            )

            if result.returncode != 0:
                return results

            current_key = None

            for line in result.stdout.splitlines():

                line = line.strip()

                if not line:
                    continue

                if line.startswith(
                    r"HKU\DoomsdayDetectorAmcache"
                ):
                    current_key = line
                    continue

                parts = line.split(
                    None,
                    2
                )

                if len(parts) < 3:
                    continue

                name, value_type, value = parts

                if name.lower() in (
                    "fullpath",
                    "fileid",
                    "sha1",
                    "programid"
                ):

                    results.append({
                        "key": current_key,
                        "name": name,
                        "value": value
                    })

        finally:

            subprocess.run(
                [
                    "reg",
                    "unload",
                    r"HKU\DoomsdayDetectorAmcache"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

    except Exception:
        return results

    finally:

        try:
            if os.path.exists(temp_hive):
                os.remove(temp_hive)
        except OSError:
            pass

    return results