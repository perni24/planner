import os
import tarfile
import textwrap
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from config import APP_VERSION


WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release-build.yml"


def get_python_step(name):
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    step = workflow.split(f"      - name: {name}\n", 1)[1].split("      - name:", 1)[0]
    return step, textwrap.dedent(step.split("        run: |\n", 1)[1]).rstrip()


def run_step(code, environment):
    with patch.dict(os.environ, environment), redirect_stdout(StringIO()):
        exec(compile(code, str(WORKFLOW_PATH), "exec"), {})


def test_release_version_matches_tag_and_rejects_mismatch():
    step, code = get_python_step("Check release version")
    assert "if: startsWith(github.ref, 'refs/tags/')" in step
    run_step(code, {"RELEASE_TAG": f"v{APP_VERSION}"})
    try:
        run_step(code, {"RELEASE_TAG": "v999.999.999-test-mismatch"})
    except SystemExit as error:
        assert "Version mismatch" in str(error)
    else:
        raise AssertionError("An inconsistent release tag must stop the job")


def make_archive(path, helper_mode=0o755, helper_type=tarfile.REGTYPE):
    with tarfile.open(path, "w:gz") as archive:
        for name, mode, kind in (
            ("PlannerApp/PlannerApp", 0o755, tarfile.REGTYPE),
            ("PlannerApp/_internal/PyQt6/Qt6/libexec/QtWebEngineProcess", helper_mode, helper_type),
        ):
            entry = tarfile.TarInfo(name)
            entry.mode = mode
            entry.type = kind
            archive.addfile(entry)


def test_linux_archive_check_accepts_executable_app_and_helper():
    step, code = get_python_step("Check Linux archive permissions")
    assert "if: runner.os == 'Linux'" in step
    with TemporaryDirectory(prefix="planner-release-archive-") as directory:
        archive = Path(directory) / "linux.tar.gz"
        make_archive(archive)
        run_step(code, {"ARCHIVE_PATH": str(archive)})


def test_linux_archive_check_rejects_non_executable_helper_and_directory():
    _, code = get_python_step("Check Linux archive permissions")
    with TemporaryDirectory(prefix="planner-release-permissions-") as directory:
        archive = Path(directory) / "linux.tar.gz"
        for mode, kind in ((0o644, tarfile.REGTYPE), (0o755, tarfile.DIRTYPE)):
            make_archive(archive, mode, kind)
            try:
                run_step(code, {"ARCHIVE_PATH": str(archive)})
            except SystemExit as error:
                assert "Executable permission missing" in str(error)
            else:
                raise AssertionError("Invalid helper permissions or type must stop packaging")


def test_unverified_linux_artifact_is_not_downloaded_for_public_release():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    release = workflow.split("  release:\n", 1)[1]
    assert "pattern: PlannerApp-windows" in release
    assert "files: release-assets/*.zip" in release


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
