import hashlib
import json
import os
import zipfile


# SHA-256 de muestras confirmadas manualmente.
KNOWN_DOOMSDAY_HASHES = {
    "faa422f391d9b2ebaa2332527b73b8e35e85c998f5f9dc45ec6d99fdb3b7247f",
}


def calculate_sha256(path):
    sha256 = hashlib.sha256()

    try:
        with open(path, "rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b""
            ):
                sha256.update(chunk)

        return sha256.hexdigest()

    except (OSError, PermissionError):
        return None


def read_entry(jar, names, target):
    target = target.lower()

    for name in names:
        if name.lower() == target:
            try:
                return jar.read(name).decode(
                    "utf-8",
                    errors="replace"
                )
            except Exception:
                return ""

    return ""


def add_indicator(result, text, points=0):
    result["indicators"].append(text)
    result["score"] += points


def analyze_candidate(path):

    result = {
        "valid": False,
        "sha256": None,
        "score": 0,
        "indicators": [],
        "verdict": "UNKNOWN",
    }

    if not os.path.isfile(path):
        return result

    # ==========================================
    # SHA-256
    # ==========================================

    result["sha256"] = calculate_sha256(path)

    if result["sha256"] is None:
        return result

    # ==========================================
    # KNOWN HASH
    # ==========================================

    if result["sha256"].lower() in KNOWN_DOOMSDAY_HASHES:

        result["valid"] = True
        result["score"] = 100
        result["verdict"] = "DOOMSDAY"

        result["indicators"].append(
            "Known Doomsday SHA-256"
        )

        return result

    # ==========================================
    # ARCHIVE CHECK
    # ==========================================

    try:

        if not zipfile.is_zipfile(path):
            return result

        with zipfile.ZipFile(path, "r") as archive:

            names = archive.namelist()

            lower_names = {
                name.lower()
                for name in names
            }

            result["valid"] = True

            # ==================================
            # MANIFEST
            # ==================================

            manifest = read_entry(
                archive,
                names,
                "META-INF/MANIFEST.MF"
            )

            manifest_lower = manifest.lower()

            if manifest:

                add_indicator(
                    result,
                    "Manifest present",
                    1
                )

            has_premain = (
                "premain-class:" in manifest_lower
            )

            has_retransform = (
                "can-retransform-classes: true"
                in manifest_lower
            )

            if has_premain:

                add_indicator(
                    result,
                    "Premain-Class present",
                    2
                )

            if has_retransform:

                add_indicator(
                    result,
                    "Class retransformation enabled",
                    2
                )

            # ==================================
            # FABRIC
            # ==================================

            fabric = read_entry(
                archive,
                names,
                "fabric.mod.json"
            )

            has_fabric_dd = False

            if fabric:

                add_indicator(
                    result,
                    "Fabric metadata present",
                    1
                )

                try:

                    fabric_data = json.loads(
                        fabric
                    )

                    fabric_id = str(
                        fabric_data.get(
                            "id",
                            ""
                        )
                    ).lower()

                    if fabric_id == "dd":

                        has_fabric_dd = True

                        add_indicator(
                            result,
                            "Fabric mod ID: dd",
                            2
                        )

                except (
                    json.JSONDecodeError,
                    TypeError
                ):
                    pass

            # ==================================
            # FORGE
            # ==================================

            mcmod = read_entry(
                archive,
                names,
                "mcmod.info"
            )

            has_forge_dd = False

            if mcmod:

                add_indicator(
                    result,
                    "Forge metadata present",
                    1
                )

                try:

                    mcmod_data = json.loads(
                        mcmod
                    )

                    if isinstance(
                        mcmod_data,
                        list
                    ):
                        entries = mcmod_data
                    else:
                        entries = [
                            mcmod_data
                        ]

                    for entry in entries:

                        if not isinstance(
                            entry,
                            dict
                        ):
                            continue

                        modid = str(
                            entry.get(
                                "modid",
                                ""
                            )
                        ).lower()

                        if modid == "dd":

                            has_forge_dd = True

                            add_indicator(
                                result,
                                "Forge mod ID: dd",
                                2
                            )

                            break

                except (
                    json.JSONDecodeError,
                    TypeError
                ):
                    pass

            # ==================================
            # JAVA CLASSES
            # ==================================

            java_classes = [
                name
                for name in lower_names
                if (
                    name.startswith(
                        "net/java/"
                    )
                    and
                    name.endswith(
                        ".class"
                    )
                )
            ]

            has_java = bool(
                java_classes
            )

            if has_java:

                add_indicator(
                    result,
                    "net/java classes: "
                    f"{len(java_classes)}",
                    1
                )

            # ==================================
            # STRUCTURAL ASSESSMENT
            # ==================================

            has_dd = (
                has_fabric_dd
                or
                has_forge_dd
            )

            strong_structure = (
                has_premain
                and
                has_retransform
                and
                has_dd
                and
                has_java
            )

            if strong_structure:

                result["indicators"].append(
                    "Strong structural candidate"
                )

            # ==================================
            # VERDICT
            # ==================================

            # IMPORTANT:
            #
            # Structural similarities do NOT make
            # a file a confirmed Doomsday sample.
            #
            # Only a known SHA-256 gets CONFIRMED.

            if strong_structure:

                result["verdict"] = (
                    "SUSPICIOUS"
                )

            elif result["score"] >= 4:

                result["verdict"] = (
                    "SUSPICIOUS"
                )

            else:

                result["verdict"] = (
                    "NORMAL"
                )

    except (
        OSError,
        PermissionError,
        zipfile.BadZipFile,
        RuntimeError,
    ):
        return result

    return result