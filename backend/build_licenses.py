import hashlib
from importlib import metadata
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import sysconfig

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


LINUX_QT_DISTRIBUTIONS = (
    "QtPy",
    "PyQt6",
    "PyQt6-sip",
    "PyQt6-WebEngine",
    "PyQt6-Qt6",
    "PyQt6-WebEngine-Qt6",
)
# Pacchetti che non distribuiscono file di licenza: il manifest registra la licenza
# dichiarata nei metadati e THIRD_PARTY_NOTICES.md riporta autore e sorgente.
DISTRIBUTIONS_WITHOUT_LICENSE_FILES = ("proxy-tools",)
RUNTIME_MANIFEST = "runtime-manifest.json"
SYSTEM_MANIFEST = "system-manifest.json"
THIRD_PARTY_LICENSES_DIR = Path(__file__).resolve().parent / "third_party_licenses"
# Versione del WebView2 SDK incluso in pywebview a cui si riferiscono i testi in
# third_party_licenses/microsoft-webview2 (LICENSE.txt e NOTICE.txt del pacchetto NuGet).
WEBVIEW2_SDK_VERSION = "1.0.3856.49"
WEBVIEW2_SDK_DLL = PurePosixPath("webview/lib/Microsoft.Web.WebView2.Core.dll")
# Avvisi generati dai sorgenti di questa versione di Qt: Chromium con
# qtwebengine_notices.py, gli altri moduli con qt_notices.py. PyQt6-Qt6 e
# PyQt6-WebEngine-Qt6 nel bundle devono corrispondere.
QT_NOTICES_VERSION = "6.11.2"
QTWEBENGINE_NOTICES = THIRD_PARTY_LICENSES_DIR / "qtwebengine" / "CHROMIUM_NOTICES.txt"
QT_NOTICES = THIRD_PARTY_LICENSES_DIR / "qt" / "QT_NOTICES.txt"
# ICU compilata da Qt e inclusa nelle wheel (libicu*.so.73), licenza della release 73.2.
QT_ICU_LICENSE = THIRD_PARTY_LICENSES_DIR / "qt" / "ICU_LICENSE.txt"
QT_ICU_MAJOR = "73"
QT_LIB_DIR = PurePosixPath("PyQt6/Qt6/lib")
# Modulo sorgente di ogni libreria Qt del bundle Linux: se ne compare una nuova, va
# aggiunto il modulo agli avvisi (qt_notices.py) prima di distribuirla.
QT_LIBRARY_MODULES = {
    **dict.fromkeys((
        "Core", "DBus", "EglFSDeviceIntegration", "Gui", "Network", "OpenGL",
        "OpenGLWidgets", "PrintSupport", "Widgets", "XcbQpa",
    ), "qtbase"),
    **dict.fromkeys(("Qml", "QmlMeta", "QmlModels", "QmlWorkerScript", "Quick", "QuickWidgets"), "qtdeclarative"),
    **dict.fromkeys(("WebEngineCore", "WebEngineWidgets", "Pdf"), "qtwebengine"),
    **dict.fromkeys(("WaylandClient", "WlShellIntegration"), "qtwayland"),
    "Positioning": "qtpositioning",
    "SerialPort": "qtserialport",
    "Svg": "qtsvg",
    "WebChannel": "qtwebchannel",
}
# libpython e coperta dalla licenza di Python in licenses/python/python.
NON_SYSTEM_LIBRARY_PREFIXES = ("libpython",)


def is_license_file(path):
    name = path.name.lower()
    return name.startswith(("license", "licence", "copying", "notice", "copyright", "authors"))


def has_license_text(files):
    return any(
        PurePosixPath(entry["path"]).name.lower().startswith(("license", "licence", "copying"))
        for entry in files
    )


def copy_license_file(source, destination, portable_dir):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "path": destination.relative_to(portable_dir).as_posix(),
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }


def copy_distribution_licenses(distribution, name, destination_dir, portable_dir):
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
        files.append(copy_license_file(source, destination_dir / relative, portable_dir))
    return files


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
        files = copy_distribution_licenses(
            distribution, name, portable_dir / "licenses" / name, portable_dir
        )
        if not has_license_text(files):
            raise RuntimeError(f"No upstream license files found for {name}")
        components.append({
            "name": name,
            "version": distribution.version,
            "source": f"https://pypi.org/project/{name}/{distribution.version}/",
            "files": files,
        })
    for component in components:
        if component["name"] in ("PyQt6-Qt6", "PyQt6-WebEngine-Qt6") and component["version"] != QT_NOTICES_VERSION:
            raise RuntimeError(
                f"Bundled {component['name']} {component['version']} does not match the Qt and Chromium "
                f"notices for {QT_NOTICES_VERSION}: regenerate them with qt_notices.py and qtwebengine_notices.py"
            )
    check_qt_notices_coverage(internal)
    major_minor = ".".join(QT_NOTICES_VERSION.split(".")[:2])
    manifest = {
        "scope": "Linux Qt packages, Qt module, ICU and Qt WebEngine (Chromium) notices",
        "qt_sources": f"https://download.qt.io/official_releases/qt/{major_minor}/{QT_NOTICES_VERSION}/",
        "chromium_notices": copy_license_file(
            QTWEBENGINE_NOTICES, portable_dir / "licenses" / "qtwebengine" / QTWEBENGINE_NOTICES.name, portable_dir
        ),
        "qt_notices": [
            copy_license_file(source, portable_dir / "licenses" / "qt" / source.name, portable_dir)
            for source in (QT_NOTICES, QT_ICU_LICENSE)
        ],
        "components": components,
    }
    manifest_path = portable_dir / "licenses" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def get_noticed_qt_modules():
    # I moduli coperti sono quelli degli archivi elencati in testa a QT_NOTICES.txt.
    header = QT_NOTICES.read_text(encoding="utf-8").split("=" * 80, 1)[0]
    modules = set(re.findall(r"^- [0-9a-f]{64}\s+(qt[a-z0-9]+)-everywhere-src-", header, re.MULTILINE))
    return modules | {"qtwebengine"}


def check_qt_notices_coverage(internal):
    noticed = get_noticed_qt_modules()
    problems = []
    for path in sorted((internal / QT_LIB_DIR).glob("*.so*")):
        name = path.name.split(".so")[0]
        if name.startswith("libicu"):
            if not path.name.split(".so.")[-1].startswith(QT_ICU_MAJOR):
                problems.append(f"{path.name} (ICU license is for {QT_ICU_MAJOR})")
            continue
        module = QT_LIBRARY_MODULES.get(name.removeprefix("libQt6"))
        if module not in noticed:
            problems.append(f"{path.name} ({module or 'unknown module'})")
    if problems:
        raise RuntimeError("Qt libraries not covered by the Qt notices: " + ", ".join(problems))


def validate_inventory_files(portable_dir, files):
    for entry in files:
        relative = PurePosixPath(entry["path"])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("licenses",):
            raise ValueError("Unsafe license inventory path")
        content = (portable_dir / relative).read_bytes()
        if not content or hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ValueError("License content does not match inventory")


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
            validate_inventory_files(portable_dir, component["files"])
        validate_inventory_files(portable_dir, [manifest["chromium_notices"], *manifest["qt_notices"]])
        if len(manifest["qt_notices"]) != 2:
            raise ValueError("Qt notices missing")
        if not manifest["qt_sources"].startswith("https://download.qt.io/"):
            raise ValueError("Qt source location missing")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"Incomplete or invalid Linux license materials: {manifest_path}") from error


def read_requirements(requirements_path):
    requirements = []
    for line in Path(requirements_path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        requirement = Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate():
            requirements.append(requirement)
    return requirements


def get_runtime_distributions(requirements_path):
    # PyInstaller impacchetta i moduli dell'ambiente che esegue la build: le dipendenze
    # (con marcatori ed extra valutati per questo sistema) si leggono dagli stessi metadati.
    pending = read_requirements(requirements_path)
    distributions = {}
    expanded_extras = {}
    while pending:
        requirement = pending.pop()
        name = canonicalize_name(requirement.name)
        # Lo stesso pacchetto puo essere richiesto con extra diversi (es. pyjwt[crypto]).
        new_extras = ({""} | set(requirement.extras)) - expanded_extras.get(name, set())
        if not new_extras:
            continue
        if name not in distributions:
            try:
                distributions[name] = metadata.distribution(requirement.name)
            except metadata.PackageNotFoundError as error:
                raise RuntimeError(f"Runtime dependency not installed: {requirement.name}") from error
        expanded_extras.setdefault(name, set()).update(new_extras)
        for dependency in distributions[name].requires or ():
            dependency = Requirement(dependency)
            if dependency.marker is None:
                if "" in new_extras:
                    pending.append(dependency)
            elif any(dependency.marker.evaluate({"extra": extra}) for extra in new_extras):
                pending.append(dependency)
    return [distributions[name] for name in sorted(distributions)]


def get_declared_license(distribution):
    info = distribution.metadata
    declared = info.get("License-Expression") or (info.get("License") or "").strip()
    if declared and "\n" not in declared and len(declared) <= 80:
        return declared
    classifiers = [
        classifier.split(" :: ")[-1]
        for classifier in info.get_all("Classifier") or ()
        if classifier.startswith("License :: ")
    ]
    return ", ".join(classifiers) or "See license files"


def find_python_license():
    for path in (
        Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
        Path(sys.base_prefix) / "LICENSE.txt",
    ):
        if path.is_file() and path.stat().st_size:
            return path
    raise RuntimeError("Python license file not found for the build interpreter")


def read_file_version(path):
    # Legge FileVersion dalle risorse di versione di una DLL Windows, anche su Linux.
    data = path.read_bytes()
    start = data.find("StringFileInfo".encode("utf-16-le"))
    key = "FileVersion".encode("utf-16-le") + b"\x00\x00"
    index = data.find(key, start) if start >= 0 else -1
    if index < 0:
        raise RuntimeError(f"File version not found: {path}")
    index += len(key)
    while data[index:index + 2] == b"\x00\x00":
        index += 2
    end = index
    while end < len(data) and data[end:end + 2] != b"\x00\x00":
        end += 2
    return data[index:end].decode("utf-16-le")


def collect_webview2_licenses(portable_dir):
    dll = portable_dir / "_internal" / WEBVIEW2_SDK_DLL
    version = read_file_version(dll)
    if version != WEBVIEW2_SDK_VERSION:
        raise RuntimeError(
            f"Bundled WebView2 SDK {version} does not match the license files for "
            f"{WEBVIEW2_SDK_VERSION}: update third_party_licenses/microsoft-webview2"
        )
    files = [
        copy_license_file(source, portable_dir / "licenses" / "microsoft-webview2" / source.name, portable_dir)
        for source in sorted((THIRD_PARTY_LICENSES_DIR / "microsoft-webview2").glob("*.txt"))
    ]
    if not has_license_text(files):
        raise RuntimeError("WebView2 SDK license file missing")
    return {
        "name": "Microsoft.Web.WebView2",
        "version": version,
        "license": "BSD-3-Clause (Microsoft)",
        "source": f"https://www.nuget.org/packages/Microsoft.Web.WebView2/{version}",
        "files": files,
    }


def collect_runtime_licenses(portable_dir, requirements_path, frontend_dir, platform=None):
    platform = sys.platform if platform is None else platform
    licenses_dir = portable_dir / "licenses"
    qt_names = {canonicalize_name(name) for name in LINUX_QT_DISTRIBUTIONS}
    components = []
    for distribution in get_runtime_distributions(requirements_path):
        name = distribution.metadata["Name"]
        canonical = canonicalize_name(name)
        if canonical in qt_names:
            # Su Linux i pacchetti Qt sono gia raccolti dai metadati del bundle.
            continue
        files = copy_distribution_licenses(
            distribution, name, licenses_dir / "python" / canonical, portable_dir
        )
        if not has_license_text(files) and canonical not in DISTRIBUTIONS_WITHOUT_LICENSE_FILES:
            raise RuntimeError(f"No upstream license files found for {name}")
        components.append({
            "name": name,
            "version": distribution.version,
            "license": get_declared_license(distribution),
            "source": f"https://pypi.org/project/{name}/{distribution.version}/",
            "files": files,
        })

    python_license = find_python_license()
    components.append({
        "name": "Python",
        "version": sys.version.split()[0],
        "license": "PSF-2.0",
        "source": "https://www.python.org/downloads/source/",
        "files": [copy_license_file(
            python_license, licenses_dir / "python" / "python" / "LICENSE.txt", portable_dir
        )],
    })

    frontend_files = []
    for source, destination in (
        # Licenze delle librerie JavaScript incluse nel bundle, generate da Vite.
        (frontend_dir / "dist" / ".vite" / "license.md", "license.md"),
        # Il CSS generato contiene codice di Tailwind, che Vite non elenca.
        (frontend_dir / "node_modules" / "tailwindcss" / "LICENSE", "tailwindcss-LICENSE"),
    ):
        if not source.is_file() or source.stat().st_size == 0:
            raise RuntimeError(f"Frontend license file missing or empty: {source}")
        frontend_files.append(
            copy_license_file(source, licenses_dir / "frontend" / destination, portable_dir)
        )
    components.append({
        "name": "frontend",
        "version": "",
        "license": "See license files",
        "source": "https://www.npmjs.com/",
        "files": frontend_files,
    })
    if platform == "win32":
        components.append(collect_webview2_licenses(portable_dir))

    manifest = {
        "scope": "Python packages, Python runtime and frontend libraries bundled in this build",
        "components": components,
    }
    manifest_path = licenses_dir / RUNTIME_MANIFEST
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate_runtime_licenses(portable_dir, platform=None):
    platform = sys.platform if platform is None else platform
    manifest_path = portable_dir / "licenses" / RUNTIME_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        components = manifest["components"]
        names = {component["name"] for component in components}
        required = {"Python", "frontend"}
        if platform == "win32":
            required.add("Microsoft.Web.WebView2")
        if not required <= names or len(names) < len(required) + 1:
            raise ValueError("Incomplete runtime license inventory")
        for component in components:
            exempt = canonicalize_name(component["name"]) in DISTRIBUTIONS_WITHOUT_LICENSE_FILES
            if not component["license"] or (not component["files"] and not exempt):
                raise ValueError("Empty runtime license inventory")
            validate_inventory_files(portable_dir, component["files"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"Incomplete or invalid runtime license materials: {manifest_path}") from error


def list_system_libraries(portable_dir):
    # PyInstaller copia in _internal/ le librerie native richieste dal bundle; i moduli
    # di estensione Python e le librerie delle wheel (anche quando PyInstaller le
    # replica in _internal/, come ICU di Qt) hanno gia le proprie licenze.
    internal = portable_dir / "_internal"
    from_packages = {
        path.name for path in internal.glob("*/**/*") if path.is_file() and ".so" in path.name
    }
    return sorted(
        path.name for path in internal.iterdir()
        if path.is_file()
        and ".so" in path.name
        and ".cpython-" not in path.name
        and not path.name.endswith(".abi3.so")
        and not path.name.startswith(NON_SYSTEM_LIBRARY_PREFIXES)
        and path.name not in from_packages
    )


def run_dpkg_query(arguments):
    try:
        result = subprocess.run(
            ["dpkg-query", *arguments], capture_output=True, text=True, check=False
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "System library license inventory requires dpkg-query (Debian or Ubuntu build machine)"
        ) from error
    return result.stdout


def file_sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").digest()


def find_library_packages(libraries, internal_dir, query, system_root):
    # "dpkg-query -S" restituisce righe "pacchetto:arch: /percorso"; un nome non
    # trovato produce solo un messaggio su stderr.
    output = query(["-S", *(f"*/{name}" for name in libraries)])
    candidates = {name: [] for name in libraries}
    for line in output.splitlines():
        if line.startswith("diversion ") or ": " not in line:
            continue
        packages, path = line.rsplit(": ", 1)
        source = PurePosixPath(path)
        if source.name in candidates and path.startswith(("/lib", "/usr/lib")):
            candidates[source.name].append((system_root / source.relative_to("/"), packages.split(", ")))

    owners = {}
    for name, paths in candidates.items():
        # Pacchetti diversi possono distribuire lo stesso nome con binari diversi.
        bundled_hash = file_sha256(internal_dir / name)
        matches = {
            package
            for path, packages in paths
            if path.is_file() and file_sha256(path) == bundled_hash
            for package in packages
        }
        if len(matches) > 1:
            raise RuntimeError(f"Ambiguous system package for {name}: {', '.join(sorted(matches))}")
        if matches:
            owners[name] = matches.pop()
    missing = sorted(set(libraries) - set(owners))
    if missing:
        raise RuntimeError(
            "No matching system package for bundled libraries: " + ", ".join(missing)
        )
    return owners


def read_os_release(path):
    values = {}
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            values[key] = value.strip().strip('"')
    except OSError:
        pass
    return values


def get_source_url(distribution_id, source_package, source_version):
    if distribution_id == "ubuntu":
        return f"https://launchpad.net/ubuntu/+source/{source_package}/{source_version}"
    if distribution_id == "debian":
        return f"https://snapshot.debian.org/package/{source_package}/{source_version}/"
    return ""


def collect_system_licenses(
    portable_dir, query=run_dpkg_query, doc_dir=Path("/usr/share/doc"), os_release="/etc/os-release",
    *, system_root=Path("/"),
):
    libraries = list_system_libraries(portable_dir)
    owners = find_library_packages(libraries, portable_dir / "_internal", query, system_root) if libraries else {}
    release = read_os_release(os_release)
    packages = sorted(set(owners.values()))
    details = {}
    if packages:
        output = query([
            "-W", "-f", "${binary:Package}\\t${Version}\\t${source:Package}\\t${source:Version}\\n", *packages,
        ])
        for line in output.splitlines():
            package, version, source_package, source_version = line.split("\t")
            details.setdefault(package, (version, source_package, source_version))
    components = []
    for owner in packages:
        if owner not in details:
            raise RuntimeError(f"System package metadata missing: {owner}")
        version, source_package, source_version = details[owner]
        package = owner.split(":", 1)[0]
        copyright_path = doc_dir / package / "copyright"
        if not copyright_path.is_file() or copyright_path.stat().st_size == 0:
            raise RuntimeError(f"License file missing or empty for system package {package}")
        components.append({
            "package": package,
            "version": version,
            "source_package": source_package,
            "source_version": source_version,
            "source": get_source_url(release.get("ID"), source_package, source_version),
            "libraries": sorted(name for name, library_owner in owners.items() if library_owner == owner),
            "files": [copy_license_file(
                copyright_path, portable_dir / "licenses" / "system" / package / "copyright", portable_dir
            )],
        })
    manifest = {
        "scope": "Native libraries copied from the build system by PyInstaller",
        "distribution": release.get("PRETTY_NAME", "unknown"),
        "components": components,
    }
    manifest_path = portable_dir / "licenses" / SYSTEM_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate_system_licenses(portable_dir):
    manifest_path = portable_dir / "licenses" / SYSTEM_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        listed = set()
        for component in manifest["components"]:
            if not component["files"] or not component["libraries"]:
                raise ValueError("Empty system license inventory")
            validate_inventory_files(portable_dir, component["files"])
            listed.update(component["libraries"])
        if not set(list_system_libraries(portable_dir)) <= listed:
            raise ValueError("Bundled system libraries missing from inventory")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"Incomplete or invalid system license materials: {manifest_path}") from error
