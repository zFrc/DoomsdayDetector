import zipfile
import hashlib
import os


def analyze_jar(path):
    result = {
        "is_jar": False,
        "sha256": None,
        "score": 0,
        "indicators": []
    }

    if not os.path.isfile(path):
        return result

    try:
        if not zipfile.is_zipfile(path):
            return result

        result["is_jar"] = True

        sha256 = hashlib.sha256()

        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        result["sha256"] = sha256.hexdigest()

        with zipfile.ZipFile(path, "r") as jar:
            files = jar.namelist()
            files_lower = {name.lower() for name in files}

            manifest = ""

            if "meta-inf/manifest.mf" in files_lower:
                for name in files:
                    if name.lower() == "meta-inf/manifest.mf":
                        manifest = jar.read(name).decode(
                            errors="replace"
                        )
                        break

            manifest_lower = manifest.lower()

            if "meta-inf/manifest.mf" in files_lower:
                result["score"] += 1
                result["indicators"].append(
                    "JAR manifest present"
                )

            if "premain-class:" in manifest_lower:
                result["score"] += 3
                result["indicators"].append(
                    "Premain-Class present"
                )

            if "can-retransform-classes: true" in manifest_lower:
                result["score"] += 2
                result["indicators"].append(
                    "Class retransformation enabled"
                )

            if "fabric.mod.json" in files_lower:
                result["score"] += 1
                result["indicators"].append(
                    "Fabric metadata present"
                )

            if "mcmod.info" in files_lower:
                result["score"] += 1
                result["indicators"].append(
                    "Forge metadata present"
                )

            class_count = sum(
                name.endswith(".class")
                for name in files_lower
            )

            if class_count:
                result["score"] += 1
                result["indicators"].append(
                    f"{class_count} Java class files"
                )

    except (OSError, zipfile.BadZipFile, PermissionError):
        return result

    return result