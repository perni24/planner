import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from build_licenses import (
    LINUX_QT_DISTRIBUTIONS,
    QTWEBENGINE_NOTICES,
    QT_ICU_LICENSE,
    QT_NOTICES,
    QT_NOTICES_VERSION,
    THIRD_PARTY_LICENSES_DIR,
    WEBVIEW2_SDK_DLL,
    WEBVIEW2_SDK_VERSION,
    collect_linux_licenses,
    collect_runtime_licenses,
    check_qt_notices_coverage,
    collect_system_licenses,
    get_runtime_distributions,
    read_file_version,
    validate_linux_licenses,
    validate_runtime_licenses,
    validate_system_licenses,
)
import webview


def make_metadata(root, version=QT_NOTICES_VERSION):
    for name in LINUX_QT_DISTRIBUTIONS:
        relative = f"{name.lower().replace('-', '_')}-{version}.dist-info"
        info = root / "_internal" / relative
        (info / "licenses").mkdir(parents=True)
        (info / "METADATA").write_text(f"Name: {name}\nVersion: {version}\n", encoding="utf-8")
        (info / "licenses" / "LICENSE.txt").write_bytes(b"Copyright upstream\nLicense text\n")
        (info / "NOTICE").write_bytes(b"Additional upstream notice\n")
        (info / "RECORD").write_text(
            f"{relative}/licenses/LICENSE.txt,,\n{relative}/NOTICE,,\n{relative}/METADATA,,\n",
            encoding="utf-8",
        )


def expect_error(operation, message):
    try:
        operation()
    except RuntimeError as error:
        assert message in str(error), str(error)
    else:
        raise AssertionError("Incomplete license materials must stop the build")


def test_collection_preserves_exact_materials_and_records_bundled_versions():
    with TemporaryDirectory(prefix="planner-licenses-") as directory:
        root = Path(directory)
        make_metadata(root)
        collect_linux_licenses(root)
        validate_linux_licenses(root)
        manifest = json.loads((root / "licenses" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["qt_sources"].endswith(f"/{QT_NOTICES_VERSION}/")
        notices = root / manifest["chromium_notices"]["path"]
        assert notices.read_bytes() == QTWEBENGINE_NOTICES.read_bytes()
        copied = {Path(entry["path"]).name: root / entry["path"] for entry in manifest["qt_notices"]}
        assert copied["QT_NOTICES.txt"].read_bytes() == QT_NOTICES.read_bytes()
        assert copied["ICU_LICENSE.txt"].read_bytes() == QT_ICU_LICENSE.read_bytes()
        assert len(manifest["components"]) == len(LINUX_QT_DISTRIBUTIONS)
        for component in manifest["components"]:
            assert component["version"] == QT_NOTICES_VERSION
            assert component["source"].endswith(f"/{QT_NOTICES_VERSION}/")
            assert len(component["files"]) == 2
            for entry in component["files"]:
                copied = root / entry["path"]
                upstream = root / "_internal" / Path(*Path(entry["path"]).parts[2:])
                assert copied.read_bytes() == upstream.read_bytes()
                assert entry["sha256"] == hashlib.sha256(upstream.read_bytes()).hexdigest()


def test_missing_metadata_prevents_successful_license_inventory():
    with TemporaryDirectory(prefix="planner-license-missing-") as directory:
        root = Path(directory)
        expect_error(lambda: collect_linux_licenses(root), "metadata missing")
        assert not (root / "licenses" / "manifest.json").exists()


def test_missing_or_empty_upstream_license_is_rejected():
    with TemporaryDirectory(prefix="planner-license-empty-") as directory:
        root = Path(directory)
        make_metadata(root)
        source = next((root / "_internal").glob("qtpy-*.dist-info/licenses/LICENSE.txt"))
        source.write_bytes(b"")
        expect_error(lambda: collect_linux_licenses(root), "missing or empty")
        source.unlink()
        expect_error(lambda: collect_linux_licenses(root), "No upstream license files")


def test_absent_license_entries_do_not_count_as_complete_materials():
    with TemporaryDirectory(prefix="planner-license-record-") as directory:
        root = Path(directory)
        make_metadata(root)
        record = next((root / "_internal").glob("qtpy-*.dist-info/RECORD"))
        record.write_text("", encoding="utf-8")
        expect_error(lambda: collect_linux_licenses(root), "No upstream license files")


def test_final_validation_rejects_missing_inventory_or_modified_license():
    with TemporaryDirectory(prefix="planner-license-integrity-") as directory:
        root = Path(directory)
        expect_error(lambda: validate_linux_licenses(root), "invalid Linux license")
        make_metadata(root)
        collect_linux_licenses(root)
        manifest_path = root / "licenses" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = root / manifest["components"][0]["files"][0]["path"]
        entry.write_bytes(b"modified")
        expect_error(lambda: validate_linux_licenses(root), "invalid Linux license")
        entry.unlink()
        expect_error(lambda: validate_linux_licenses(root), "invalid Linux license")


def make_runtime_sources(root, requirements="starlette\n"):
    (root / "requirements.txt").write_text(requirements, encoding="utf-8")
    sources = {
        "dist/.vite/license.md": b"## react - 19.0.0 (MIT)\n",
        "node_modules/tailwindcss/LICENSE": b"MIT License\n",
    }
    for relative, content in sources.items():
        path = root / "frontend" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return root / "requirements.txt", root / "frontend"


def test_runtime_dependencies_follow_markers_extras_and_transitive_requirements():
    with TemporaryDirectory(prefix="planner-runtime-deps-") as directory:
        requirements, _ = make_runtime_sources(
            Path(directory),
            "# commento\n-r other.txt\nstarlette\nmcp\nnot-installed; sys_platform == 'never'\n",
        )
        names = {distribution.metadata["Name"].lower() for distribution in get_runtime_distributions(requirements)}
        # anyio arriva da starlette, cryptography dall'extra pyjwt[crypto] richiesto da mcp.
        assert {"starlette", "anyio", "mcp", "pyjwt", "cryptography"} <= names
        assert "not-installed" not in names


def test_missing_runtime_dependency_stops_the_inventory():
    with TemporaryDirectory(prefix="planner-runtime-missing-") as directory:
        root = Path(directory)
        requirements, frontend = make_runtime_sources(root, "planner-package-that-does-not-exist\n")
        expect_error(lambda: collect_runtime_licenses(root, requirements, frontend), "not installed")


def test_runtime_collection_copies_python_and_frontend_licenses():
    with TemporaryDirectory(prefix="planner-runtime-licenses-") as directory:
        root = Path(directory)
        requirements, frontend = make_runtime_sources(root)
        collect_runtime_licenses(root, requirements, frontend)
        validate_runtime_licenses(root)
        manifest = json.loads((root / "licenses" / "runtime-manifest.json").read_text(encoding="utf-8"))
        components = {component["name"].lower(): component for component in manifest["components"]}
        assert {"starlette", "anyio", "python", "frontend"} <= set(components)
        assert components["starlette"]["license"] == "BSD-3-Clause"
        for component in components.values():
            assert component["files"]
            for entry in component["files"]:
                copied = root / entry["path"]
                assert entry["sha256"] == hashlib.sha256(copied.read_bytes()).hexdigest()
        frontend_files = {Path(entry["path"]).name for entry in components["frontend"]["files"]}
        assert frontend_files == {"license.md", "tailwindcss-LICENSE"}


def test_runtime_collection_requires_frontend_license_files():
    with TemporaryDirectory(prefix="planner-runtime-frontend-") as directory:
        root = Path(directory)
        requirements, frontend = make_runtime_sources(root)
        (frontend / "dist" / ".vite" / "license.md").unlink()
        expect_error(lambda: collect_runtime_licenses(root, requirements, frontend), "Frontend license")
        assert not (root / "licenses" / "runtime-manifest.json").exists()


def test_runtime_validation_rejects_missing_or_modified_license():
    with TemporaryDirectory(prefix="planner-runtime-integrity-") as directory:
        root = Path(directory)
        expect_error(lambda: validate_runtime_licenses(root), "invalid runtime license")
        requirements, frontend = make_runtime_sources(root)
        collect_runtime_licenses(root, requirements, frontend)
        copied = root / "licenses" / "frontend" / "license.md"
        copied.write_bytes(b"modified")
        expect_error(lambda: validate_runtime_licenses(root), "invalid runtime license")
        copied.unlink()
        expect_error(lambda: validate_runtime_licenses(root), "invalid runtime license")


def test_chromium_notices_match_the_configured_qt_webengine_version():
    header = QTWEBENGINE_NOTICES.read_text(encoding="utf-8").splitlines()[0]
    assert header == f"Third-party notices for Qt WebEngine {QT_NOTICES_VERSION} (Chromium)"
    requirements = (Path(__file__).resolve().parents[1] / "requirements.txt").read_text(encoding="utf-8")
    assert f"PyQt6-WebEngine-Qt6=={QT_NOTICES_VERSION};" in requirements


def test_different_qt_webengine_version_requires_new_chromium_notices():
    with TemporaryDirectory(prefix="planner-license-chromium-") as directory:
        root = Path(directory)
        make_metadata(root, "6.99.0")
        expect_error(lambda: collect_linux_licenses(root), "Chromium notices")


def test_webview2_license_files_match_the_sdk_bundled_by_pywebview():
    bundled = Path(webview.__file__).parent / WEBVIEW2_SDK_DLL.relative_to("webview")
    assert read_file_version(bundled) == WEBVIEW2_SDK_VERSION
    names = {path.name for path in (THIRD_PARTY_LICENSES_DIR / "microsoft-webview2").iterdir()}
    assert names == {"LICENSE.txt", "NOTICE.txt"}


def make_webview2_dll(root, version):
    dll = root / "_internal" / WEBVIEW2_SDK_DLL
    dll.parent.mkdir(parents=True, exist_ok=True)
    dll.write_bytes(b"".join(
        text.encode("utf-16-le") + b"\x00\x00" for text in ("StringFileInfo", "FileVersion", version)
    ))


def test_windows_runtime_inventory_includes_webview2_sdk_notices():
    with TemporaryDirectory(prefix="planner-runtime-webview2-") as directory:
        root = Path(directory)
        requirements, frontend = make_runtime_sources(root)
        make_webview2_dll(root, WEBVIEW2_SDK_VERSION)
        collect_runtime_licenses(root, requirements, frontend, "win32")
        validate_runtime_licenses(root, "win32")
        manifest = json.loads((root / "licenses" / "runtime-manifest.json").read_text(encoding="utf-8"))
        webview2 = next(c for c in manifest["components"] if c["name"] == "Microsoft.Web.WebView2")
        assert {Path(entry["path"]).name for entry in webview2["files"]} == {"LICENSE.txt", "NOTICE.txt"}
        (root / "licenses" / "microsoft-webview2" / "NOTICE.txt").write_bytes(b"modified")
        expect_error(lambda: validate_runtime_licenses(root, "win32"), "invalid runtime license")


def test_different_webview2_sdk_requires_updated_license_files():
    with TemporaryDirectory(prefix="planner-runtime-webview2-version-") as directory:
        root = Path(directory)
        requirements, frontend = make_runtime_sources(root)
        make_webview2_dll(root, "1.0.1.0")
        expect_error(lambda: collect_runtime_licenses(root, requirements, frontend, "win32"), "WebView2 SDK")


def fake_dpkg(owners, details):
    def query(arguments):
        if arguments[0] == "-S":
            return "".join(
                f"{owners[pattern[2:]]}:amd64: /usr/lib/x86_64-linux-gnu/{pattern[2:]}\n"
                for pattern in arguments[1:] if pattern[2:] in owners
            )
        return "".join(f"{package}\t{details[package]}\n" for package in arguments[3:])
    return query


def make_system_bundle(root, libraries):
    internal = root / "_internal"
    internal.mkdir(parents=True)
    # libpython, moduli di estensione e librerie replicate dalle wheel non sono di sistema.
    (internal / "PyQt6" / "Qt6" / "lib").mkdir(parents=True)
    (internal / "PyQt6" / "Qt6" / "lib" / "libicudata.so.73").write_bytes(b"\x7fELF")
    for name in (
        *libraries, "libpython3.14.so.1.0", "_cffi_backend.cpython-314-x86_64-linux-gnu.so", "libicudata.so.73",
    ):
        (internal / name).write_bytes(b"\x7fELF")
    docs = root / "doc"
    for package in ("libgtk-3-0", "libssl3"):
        (docs / package).mkdir(parents=True)
        (docs / package / "copyright").write_text(f"{package} copyright\n", encoding="utf-8")
    release = root / "os-release"
    release.write_text('ID=ubuntu\nPRETTY_NAME="Ubuntu 22.04"\n', encoding="utf-8")
    return docs, release


def test_system_inventory_maps_bundled_libraries_to_packages_and_sources():
    with TemporaryDirectory(prefix="planner-system-licenses-") as directory:
        root = Path(directory)
        docs, release = make_system_bundle(root, ("libgtk-3.so.0", "libgdk-3.so.0", "libssl.so.3"))
        query = fake_dpkg(
            {"libgtk-3.so.0": "libgtk-3-0", "libgdk-3.so.0": "libgtk-3-0", "libssl.so.3": "libssl3"},
            {"libgtk-3-0": "3.24.33-1\tgtk+3.0\t3.24.33-1", "libssl3": "3.0.2-0ubuntu1\topenssl\t3.0.2-0ubuntu1"},
        )
        collect_system_licenses(root, query, docs, release)
        validate_system_licenses(root)
        manifest = json.loads((root / "licenses" / "system-manifest.json").read_text(encoding="utf-8"))
        assert manifest["distribution"] == "Ubuntu 22.04"
        components = {component["package"]: component for component in manifest["components"]}
        assert components["libgtk-3-0"]["libraries"] == ["libgdk-3.so.0", "libgtk-3.so.0"]
        assert components["libssl3"]["source"] == "https://launchpad.net/ubuntu/+source/openssl/3.0.2-0ubuntu1"
        (root / "_internal" / "libextra.so.1").write_bytes(b"\x7fELF")
        expect_error(lambda: validate_system_licenses(root), "invalid system license")


def test_system_inventory_rejects_libraries_without_package_or_license():
    with TemporaryDirectory(prefix="planner-system-missing-") as directory:
        root = Path(directory)
        docs, release = make_system_bundle(root, ("libgtk-3.so.0", "libcustom.so.1"))
        query = fake_dpkg({"libgtk-3.so.0": "libgtk-3-0"}, {"libgtk-3-0": "1\tgtk+3.0\t1"})
        expect_error(lambda: collect_system_licenses(root, query, docs, release), "libcustom.so.1")
        (root / "_internal" / "libcustom.so.1").unlink()
        (docs / "libgtk-3-0" / "copyright").unlink()
        expect_error(lambda: collect_system_licenses(root, query, docs, release), "libgtk-3-0")


def test_qt_notices_match_the_configured_qt_version():
    header = QT_NOTICES.read_text(encoding="utf-8").splitlines()[0]
    assert header == f"Third-party notices for Qt {QT_NOTICES_VERSION} modules"
    assert QT_ICU_LICENSE.read_text(encoding="utf-8").startswith("UNICODE, INC. LICENSE AGREEMENT")
    requirements = (Path(__file__).resolve().parents[1] / "requirements.txt").read_text(encoding="utf-8")
    assert f"PyQt6-Qt6=={QT_NOTICES_VERSION};" in requirements


def make_qt_libraries(root, names):
    lib = root / "_internal" / "PyQt6" / "Qt6" / "lib"
    lib.mkdir(parents=True, exist_ok=True)
    for name in names:
        (lib / name).write_bytes(b"\x7fELF")
    return root / "_internal"


def test_qt_libraries_must_be_covered_by_the_notices():
    with TemporaryDirectory(prefix="planner-qt-coverage-") as directory:
        internal = make_qt_libraries(Path(directory), (
            "libQt6Core.so.6", "libQt6WebEngineCore.so.6", "libQt6Svg.so.6", "libicuuc.so.73",
        ))
        check_qt_notices_coverage(internal)
        (internal / "PyQt6" / "Qt6" / "lib" / "libQt6Quick3D.so.6").write_bytes(b"\x7fELF")
        expect_error(lambda: check_qt_notices_coverage(internal), "libQt6Quick3D.so.6")


def test_different_icu_version_requires_updated_license():
    with TemporaryDirectory(prefix="planner-qt-icu-") as directory:
        internal = make_qt_libraries(Path(directory), ("libicuuc.so.74",))
        expect_error(lambda: check_qt_notices_coverage(internal), "ICU license")


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
