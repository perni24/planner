import hashlib
from importlib import metadata
import json
from pathlib import PurePosixPath
import shutil


LINUX_QT_DISTRIBUTIONS = (
    "QtPy",
    "PyQt6",
    "PyQt6-sip",
    "PyQt6-WebEngine",
    "PyQt6-Qt6",
    "PyQt6-WebEngine-Qt6",
)


def is_license_file(path):
    name = path.name.lower()
    return name.startswith(("license", "licence", "copying", "notice", "copyright"))


def collect_linux_licenses(portable_dir):
    # Legge i metadati del bundle, non quelli dell'interprete che avvia lo script.
    internal = portable_dir / "_internal"
    distributions = {
        distribution.metadata["Name"].lower().replace("_", "-"): distribution
        for distribution in metadata.distributions(path=[str(internal)])
    }
    components = []
    for name in LINUX_QT_DISTRIBUTIONS:
        distribution = distributions.get(name.lower())
        if distribution is None:
            raise RuntimeError(f"License metadata missing from bundle: {name}")
        files = []
        for entry in distribution.files or ():
            relative = PurePosixPath(str(entry))
            if not is_license_file(relative):
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"Unsafe license path in {name}: {relative}")
            source = distribution.locate_file(entry)
            if not source.is_file() or source.stat().st_size == 0:
                raise RuntimeError(f"License file missing or empty for {name}: {relative}")
            destination = portable_dir / "licenses" / name / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            files.append({
                "path": destination.relative_to(portable_dir).as_posix(),
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            })
        if not any(PurePosixPath(entry["path"]).name.lower().startswith(("license", "licence", "copying")) for entry in files):
            raise RuntimeError(f"No upstream license files found for {name}")
        components.append({
            "name": name,
            "version": distribution.version,
            "source": f"https://pypi.org/project/{name}/{distribution.version}/",
            "files": files,
        })
    manifest = {
        "scope": "Linux Qt packages; not a complete dependency or source-code inventory",
        "chromium_notices_review_required": True,
        "components": components,
    }
    manifest_path = portable_dir / "licenses" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate_linux_licenses(portable_dir):
    manifest_path = portable_dir / "licenses" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        components = manifest["components"]
        if {component["name"] for component in components} != set(LINUX_QT_DISTRIBUTIONS):
            raise ValueError("Incomplete Qt license inventory")
        for component in components:
            if not component["files"] or not component["version"]:
                raise ValueError("Empty Qt license inventory")
            for entry in component["files"]:
                relative = PurePosixPath(entry["path"])
                if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("licenses",):
                    raise ValueError("Unsafe license inventory path")
                content = (portable_dir / relative).read_bytes()
                if not content or hashlib.sha256(content).hexdigest() != entry["sha256"]:
                    raise ValueError("License content does not match inventory")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"Incomplete or invalid Linux license materials: {manifest_path}") from error
