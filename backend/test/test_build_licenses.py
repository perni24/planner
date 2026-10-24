import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from build_licenses import LINUX_QT_DISTRIBUTIONS, collect_linux_licenses, validate_linux_licenses


def make_metadata(root):
    for name in LINUX_QT_DISTRIBUTIONS:
        relative = f"{name.lower().replace('-', '_')}-6.11.0.dist-info"
        info = root / "_internal" / relative
        (info / "licenses").mkdir(parents=True)
        (info / "METADATA").write_text(f"Name: {name}\nVersion: 6.11.0\n", encoding="utf-8")
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
        assert manifest["chromium_notices_review_required"] is True
        assert len(manifest["components"]) == len(LINUX_QT_DISTRIBUTIONS)
        for component in manifest["components"]:
            assert component["version"] == "6.11.0"
            assert component["source"].endswith("/6.11.0/")
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


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
