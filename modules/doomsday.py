import os
import zipfile


MAX_FILE_SIZE = 20 * 1024 * 1024

SCAN_DIRS = [
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/AppData/Local/Temp"),
    os.path.expanduser("~/AppData/Roaming/.minecraft"),
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "assets",
    "libraries",
}


def quick_check(path):
    """
    Comprueba rápidamente si el archivo podría ser
    nuestro tipo de JAR sin analizar todo su contenido.
    """

    try:
        size = os.path.getsize(path)

        if size <= 0 or size > MAX_FILE_SIZE:
            return False

        with open(path, "rb") as file:
            header = file.read(4)

        # ZIP/JAR
        if header != b"PK\x03\x04":
            return False

        if not zipfile.is_zipfile(path):
            return False

        with zipfile.ZipFile(path, "r") as jar:

            names = {
                name.lower()
                for name in jar.namelist()
            }

            # Necesitamos al menos parte de la
            # estructura característica.
            has_manifest = (
                "meta-inf/manifest.mf"
                in names
            )

            has_fabric = (
                "fabric.mod.json"
                in names
            )

            has_forge = (
                "mcmod.info"
                in names
            )

            has_java = any(
                name.startswith("net/java/")
                and name.endswith(".class")
                for name in names
            )

            # No marcamos nada como Doomsday todavía.
            # Solo dejamos pasar candidatos.
            return (
                has_manifest
                and has_java
                and (has_fabric or has_forge)
            )

    except (
        OSError,
        PermissionError,
        zipfile.BadZipFile,
    ):
        return False


def scan_directory(directory):
    candidates = []
    scanned = 0

    if not os.path.exists(directory):
        return candidates, scanned

    for root, dirs, files in os.walk(
        directory,
        topdown=True,
        onerror=lambda error: None,
    ):

        dirs[:] = [
            name
            for name in dirs
            if name.lower() not in SKIP_DIRS
        ]

        for filename in files:

            scanned += 1

            path = os.path.join(
                root,
                filename
            )

            if quick_check(path):

                try:
                    candidates.append({
                        "name": filename,
                        "path": path,
                        "size": os.path.getsize(path),
                    })

                except OSError:
                    pass

    return candidates, scanned


def scan_doomsday():
    candidates = []
    scanned = 0

    for directory in SCAN_DIRS:

        found, count = scan_directory(
            directory
        )

        candidates.extend(found)
        scanned += count

    # Evitar duplicados
    unique = {}

    for candidate in candidates:
        unique[
            os.path.normcase(
                os.path.abspath(
                    candidate["path"]
                )
            )
        ] = candidate

    return {
        "candidates": list(unique.values()),
        "scanned": scanned,
    }