"""Genera gli avvisi di terze parti dei moduli Qt dai sorgenti ufficiali.

Uso (da backend/, con i sorgenti dei moduli estratti):

    python qt_notices.py <output.txt> --checksums <file.sha256> <modulo-everywhere-src-X.Y.Z> ...

<file.sha256> contiene le righe dei file .sha256 pubblicati accanto agli archivi,
verificati prima dell'estrazione. Legge i file qt_attribution.json e i testi di
licenza indicati (o quelli SPDX in LICENSES/ del modulo), senza eseguire codice dei
sorgenti. Esclude i componenti usati solo da test, esempi o strumenti.
"""

import argparse
import json
import re
from pathlib import Path

SEPARATOR = "=" * 80


def get_version(source_dir):
    match = re.fullmatch(r"(qt[a-z0-9]+)-everywhere-src-(\d+\.\d+\.\d+)", source_dir.name)
    if not match:
        raise SystemExit(f"Unexpected source directory name: {source_dir.name}")
    return match.groups()


def is_library_component(attribution_path, entry):
    parts = entry.get("QtParts")
    if parts is not None and "libs" not in parts:
        return False
    return not {"tests", "examples"} & set(attribution_path.parts)


def spdx_ids(expression):
    return [
        token for token in re.split(r"[\s()]+", expression or "")
        if token and token not in ("AND", "OR", "WITH")
    ]


def license_texts(entry, attribution_dir, module_dir):
    files = [entry[key] for key in ("LicenseFile", "CopyrightFile") if entry.get(key)]
    files += entry.get("LicenseFiles") or []
    paths = [(attribution_dir / name).resolve() for name in files]
    if not paths:
        # Senza file indicato valgono i testi SPDX del modulo (struttura REUSE).
        paths = [module_dir / "LICENSES" / f"{license_id}.txt" for license_id in spdx_ids(entry.get("LicenseId"))]
    return [path for path in paths if path.is_file()], [path for path in paths if not path.is_file()]


def collect_entries(module_dir):
    entries = []
    for attribution in sorted(module_dir.rglob("qt_attribution.json")):
        data = json.loads(attribution.read_text(encoding="utf-8"), strict=False)
        for entry in data if isinstance(data, list) else [data]:
            if not is_library_component(attribution.relative_to(module_dir), entry):
                continue
            readable, missing = license_texts(entry, attribution.parent, module_dir)
            entries.append({
                **entry,
                "path": attribution.parent.relative_to(module_dir.parent).as_posix(),
                "files": readable,
                "missing": missing,
            })
    return entries


def render(modules, checksums):
    versions = {get_version(module)[1] for module in modules}
    if len(versions) != 1:
        raise SystemExit(f"Modules from different Qt versions: {sorted(versions)}")
    version = versions.pop()
    major_minor = ".".join(version.split(".")[:2])
    lines = [
        f"Third-party notices for Qt {version} modules",
        "",
        "Generated with backend/qt_notices.py from the official source archives:",
        *(f"- {line}" for line in checksums),
        "Components used only by tests, examples or tools are omitted; the list may",
        "include components not compiled into the binaries distributed with Planner.",
        "Qt WebEngine (Chromium) has its own notices in CHROMIUM_NOTICES.txt and ICU",
        "in ICU_LICENSE.txt.",
        f"Source code: https://download.qt.io/official_releases/qt/{major_minor}/{version}/submodules/",
        "",
    ]
    missing = []
    seen = set()
    for module in modules:
        for entry in collect_entries(module):
            key = (entry["Name"], entry["path"])
            if key in seen:
                continue
            seen.add(key)
            missing += [f"{entry['Name']}: {path.name}" for path in entry["missing"]]
            title = entry["Name"] + (f" {entry['Version']}" if entry.get("Version") else "")
            copyright_text = entry.get("Copyright") or ""
            if isinstance(copyright_text, list):
                copyright_text = "\n".join(copyright_text)
            lines += [SEPARATOR, title, f"Module: {get_version(module)[0]}", f"Path: {entry['path']}"]
            for label in ("Homepage", "License"):
                if entry.get(label):
                    lines.append(f"{label}: {entry[label]}")
            if copyright_text:
                lines += ["", copyright_text.strip()]
            lines.append("-" * 80)
            for path in entry["files"]:
                lines += [path.read_text(encoding="utf-8", errors="replace").rstrip(), ""]
    if missing:
        raise SystemExit("License texts not found: " + ", ".join(missing))
    return "\n".join(lines) + "\n", len(seen)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate third-party notices from Qt module sources.")
    parser.add_argument("output", type=Path)
    parser.add_argument("modules", type=Path, nargs="+")
    parser.add_argument("--checksums", type=Path, required=True, help="sha256sum lines of the verified archives")
    args = parser.parse_args(argv)
    checksums = [line.strip() for line in args.checksums.read_text(encoding="utf-8").splitlines() if line.strip()]
    text, count = render(sorted(module.resolve() for module in args.modules), checksums)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"{count} components: {args.output}")


if __name__ == "__main__":
    main()
