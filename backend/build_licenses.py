import hashlib
from importlib import metadata
import json
from pathlib import Path, PurePosixPath
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
# Avvisi Chromium generati con qtwebengine_notices.py dai sorgenti di questa versione:
# PyQt6-WebEngine-Qt6 nel bundle deve corrispondere.
QTWEBENGINE_NOTICES_VERSION = "6.11.2"
QTWEBENGINE_NOTICES = THIRD_PARTY_LICENSES_DIR / "qtwebengine" / "CHROMIUM_NOTICES.txt"
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
    webengine_version = next(
        component["version"] for component in components if component["name"] == "PyQt6-WebEngine-Qt6"
    )
    if webengine_version != QTWEBENGINE_NOTICES_VERSION:
        raise RuntimeError(
            f"Bundled Qt WebEngine {webengine_version} does not match the Chromium notices for "
            f"{QTWEBENGINE_NOTICES_VERSION}: regenerate them with qtwebengine_notices.py"
        )
    major_minor = ".".join(webengine_version.split(".")[:2])
    manifest = {
        "scope": "Linux Qt packages and Qt WebEngine (Chromium) notices",
        "qt_sources": f"https://download.qt.io/official_releases/qt/{major_minor}/{webengine_version}/",
        "chromium_notices": copy_license_file(
            QTWEBENGINE_NOTICES, portable_dir / "licenses" / "qtwebengine" / QTWEBENGINE_NOTICES.name, portable_dir
        ),
        "components": components,
    }
    manifest_path = portable_dir / "licenses" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


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
        validate_inventory_files(portable_dir, [manifest["chromium_notices"]])
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


def find_library_packages(libraries, query):
    # "dpkg-query -S" restituisce righe "pacchetto:arch: /percorso"; un nome non
    # trovato produce solo un messaggio su stderr.
    output = query(["-S", *(f"*/{name}" for name in libraries)])
    owners = {}
    for line in output.splitlines():
        if line.startswith("diversion ") or ": " not in line:
            continue
        packages, path = line.rsplit(": ", 1)
        name = PurePosixPath(path).name
        if name in libraries and name not in owners and path.startswith(("/lib", "/usr/lib")):
            owners[name] = packages.split(", ")[0].split(":")[0]
    missing = sorted(set(libraries) - set(owners))
    if missing:
        raise RuntimeError(
            "Bundled libraries not provided by a system package: " + ", ".join(missing)
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
    portable_dir, query=run_dpkg_query, doc_dir=Path("/usr/share/doc"), os_release="/etc/os-release"
):
    libraries = list_system_libraries(portable_dir)
    owners = find_library_packages(libraries, query) if libraries else {}
    release = read_os_release(os_release)
    packages = sorted(set(owners.values()))
    details = {}
    if packages:
        output = query([
            "-W", "-f", "${Package}\\t${Version}\\t${source:Package}\\t${source:Version}\\n", *packages,
        ])
        for line in output.splitlines():
            package, version, source_package, source_version = line.split("\t")
            details.setdefault(package, (version, source_package, source_version))
    components = []
    for package in packages:
        if package not in details:
            raise RuntimeError(f"System package metadata missing: {package}")
        version, source_package, source_version = details[package]
        copyright_path = doc_dir / package / "copyright"
        if not copyright_path.is_file() or copyright_path.stat().st_size == 0:
            raise RuntimeError(f"License file missing or empty for system package {package}")
        components.append({
            "package": package,
            "version": version,
            "source_package": source_package,
            "source_version": source_version,
            "source": get_source_url(release.get("ID"), source_package, source_version),
            "libraries": sorted(name for name, owner in owners.items() if owner == package),
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
