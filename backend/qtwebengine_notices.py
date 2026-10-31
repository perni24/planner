"""Genera gli avvisi di terze parti di Chromium dai sorgenti ufficiali di QtWebEngine.

Uso (da backend/, con i sorgenti estratti):

    python qtwebengine_notices.py <qtwebengine-everywhere-src-X.Y.Z> <output.txt> --sha256 <hash>

<hash> e il valore del file .sha256 pubblicato accanto all'archivio, verificato prima
dell'estrazione.

Legge i file README.chromium e i file di licenza che indicano, senza eseguire codice
dei sorgenti. Include i componenti che non sono marcati "Shipped: no": l'elenco puo
essere piu ampio di quello effettivamente compilato da Qt, ma non lo restringe.
"""

import argparse
import re
from pathlib import Path

DEPENDENCY_DIVIDER = "-------------------- DEPENDENCY DIVIDER --------------------"
SEPARATOR = "=" * 80
FIELDS = ("Name", "URL", "Version", "License", "License File", "Shipped")


def parse_readme(text):
    # Ogni README.chromium puo descrivere piu dipendenze separate dal divisore; i campi
    # possono seguire la descrizione, quindi vale la prima occorrenza di ciascuno.
    entries = []
    for block in text.split(DEPENDENCY_DIVIDER):
        fields = {}
        for line in block.splitlines():
            match = re.match(r"^([A-Za-z][A-Za-z ]*):\s*(.*)$", line)
            if match and match.group(1).strip() in FIELDS:
                fields.setdefault(match.group(1).strip(), match.group(2).strip())
        if fields.get("Name"):
            entries.append(fields)
    return entries


def resolve_license_files(value, readme_dir, chromium_dir):
    paths = []
    for item in re.split(r"\s*,\s*", value or ""):
        if not item or item.upper() == "NOT_SHIPPED":
            continue
        if item.endswith("in Chromium/src"):
            path = chromium_dir / item.split()[0]
        elif item.startswith("//"):
            path = chromium_dir / item[2:]
        elif item.startswith("/"):
            path = chromium_dir / item[1:]
        else:
            path = readme_dir / item
        paths.append(path.resolve())
    return paths


def find_parent_license(directory, chromium_dir):
    # Senza "License File" vale il LICENSE della cartella o della piu vicina superiore
    # (es. skcms dentro Skia), fermandosi alla radice di Chromium.
    for candidate in (directory, *directory.parents):
        if (candidate / "LICENSE").is_file():
            return [candidate / "LICENSE"]
        if candidate == chromium_dir:
            break
    return []


def collect_entries(source_dir):
    chromium_dir = (source_dir / "src" / "3rdparty" / "chromium").resolve()
    entries = [{
        "Name": "The Chromium Project",
        "URL": "https://www.chromium.org",
        "License": "BSD-3-Clause",
        "path": "src/3rdparty/chromium",
        "files": [chromium_dir / "LICENSE"],
    }]
    missing = []
    for readme in sorted(source_dir.rglob("README.chromium")):
        if "tools/licenses/test_dir" in readme.as_posix():
            continue
        for fields in parse_readme(readme.read_text(encoding="utf-8", errors="replace")):
            if fields.get("Shipped", "yes").lower() == "no" or fields.get("License File", "").upper() == "NOT_SHIPPED":
                continue
            if "License File" in fields:
                files = resolve_license_files(fields["License File"], readme.parent, chromium_dir)
            else:
                files = find_parent_license(readme.parent.resolve(), chromium_dir)
            readable = [path for path in files if path.is_file()]
            if not readable:
                missing.append(f"{fields['Name']} ({readme.parent.relative_to(source_dir)})")
            entries.append({
                **fields,
                "path": readme.parent.relative_to(source_dir).as_posix(),
                "files": readable,
            })
    return entries, missing


def get_version(source_dir):
    match = re.fullmatch(r"qtwebengine-everywhere-src-(\d+)\.(\d+)\.(\d+)", source_dir.name)
    if not match:
        raise SystemExit(f"Unexpected source directory name: {source_dir.name}")
    return match.groups()


def render(source_dir, entries, missing, sha256):
    major, minor, patch = get_version(source_dir)
    lines = [
        f"Third-party notices for Qt WebEngine {major}.{minor}.{patch} (Chromium)",
        "",
        f"Generated from the official source archive {source_dir.name}.tar.xz",
        f"(SHA-256 {sha256}) with backend/qtwebengine_notices.py.",
        "Components marked \"Shipped: no\" are omitted; the list may include",
        "components not compiled into Qt WebEngine.",
        f"Source code: https://download.qt.io/official_releases/qt/{major}.{minor}/{major}.{minor}.{patch}/submodules/",
        "",
    ]
    if missing:
        lines += ["Components whose license file is not included in the Qt source archive;",
                  "most of their sources are not included either, so they are not built.",
                  "See their URL and License field:", *(f"- {item}" for item in missing), ""]
    seen = set()
    for entry in entries:
        key = (entry["Name"], tuple(entry["files"]))
        if key in seen:
            continue
        seen.add(key)
        title = entry["Name"] + (f" {entry['Version']}" if entry.get("Version") not in (None, "", "N/A") else "")
        lines += [SEPARATOR, title]
        for label in ("URL", "License"):
            if entry.get(label):
                lines.append(f"{label}: {entry[label]}")
        lines += [f"Path: {entry['path']}", "-" * 80]
        for path in entry["files"]:
            lines += [path.read_text(encoding="utf-8", errors="replace").rstrip(), ""]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate Chromium notices from Qt WebEngine sources.")
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sha256", required=True, help="SHA-256 of the verified source archive")
    args = parser.parse_args(argv)
    source_dir = args.source_dir.resolve()
    entries, missing = collect_entries(source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(source_dir, entries, missing, args.sha256), encoding="utf-8")
    print(f"{len(entries)} components, {len(missing)} without license file: {args.output}")


if __name__ == "__main__":
    main()
