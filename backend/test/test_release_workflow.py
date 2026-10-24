import os
import subprocess
import sys
import tarfile
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from config import APP_VERSION


WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release-build.yml"
BACKEND_DIR = Path(__file__).resolve().parents[1]


def get_python_step(name):
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    step = workflow.split(f"      - name: {name}\n", 1)[1].split("      - name:", 1)[0]
    return step, textwrap.dedent(step.split("        run: |\n", 1)[1]).rstrip()


def run_step(code, environment, cwd=BACKEND_DIR):
    # Come "shell: python" di GitHub Actions: lo script viene salvato in un file
    # temporaneo ed eseguito con "python <file>" dalla working-directory dello step.
    # Python cerca quindi i moduli nella cartella del file, non in cwd.
    with TemporaryDirectory(prefix="planner-runner-temp-") as runner_temp:
        script = Path(runner_temp) / "step.py"
        script.write_text(code, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script)],
            cwd=cwd,
            # Senza PYTHONPATH ereditato: il runner di GitHub non lo imposta.
            env={
                **{key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                "PYTHONDONTWRITEBYTECODE": "1",
                **environment,
            },
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )


def test_release_version_matches_tag_and_rejects_mismatch():
    step, code = get_python_step("Check release version")
    assert "if: startsWith(github.ref, 'refs/tags/')" in step
    assert "working-directory: backend" in step
    result = run_step(code, {"RELEASE_TAG": f"v{APP_VERSION}"})
    assert result.returncode == 0, result.stderr
    assert f"Release version verified: {APP_VERSION}" in result.stdout

    result = run_step(code, {"RELEASE_TAG": "v999.999.999-test-mismatch"})
    assert result.returncode != 0, "An inconsistent release tag must stop the job"
    assert "Version mismatch" in result.stderr


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
        result = run_step(code, {"ARCHIVE_PATH": str(archive)})
        assert result.returncode == 0, result.stderr


def test_linux_archive_check_rejects_non_executable_helper_and_directory():
    _, code = get_python_step("Check Linux archive permissions")
    with TemporaryDirectory(prefix="planner-release-permissions-") as directory:
        archive = Path(directory) / "linux.tar.gz"
        for mode, kind in ((0o644, tarfile.REGTYPE), (0o755, tarfile.DIRTYPE)):
            make_archive(archive, mode, kind)
            result = run_step(code, {"ARCHIVE_PATH": str(archive)})
            assert result.returncode != 0, "Invalid helper permissions or type must stop packaging"
            assert "Executable permission missing" in result.stderr


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
