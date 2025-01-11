from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from cleo.testers.application_tester import ApplicationTester

from poetry.console.application import Application


if TYPE_CHECKING:
    from tests.types import FixtureCopier


@pytest.fixture
def project_source_directory(fixture_copier: FixtureCopier) -> Path:
    return fixture_copier("up_to_date_lock")


@pytest.fixture
def tester() -> ApplicationTester:
    return ApplicationTester(Application())


@pytest.mark.parametrize("parameter", ["-C", "--directory", "-P", "--project"])
def test_application_global_option_position_does_not_matter(
    parameter: str, tester: ApplicationTester, project_source_directory: Path
) -> None:
    cwd = Path.cwd()
    assert cwd != project_source_directory

    error_string = "Poetry could not find a pyproject.toml file in"

    # command fails due to lack of pyproject.toml file in cwd
    tester.execute("show --only main")
    assert tester.status_code != 0

    stderr = tester.io.fetch_error()
    assert error_string in stderr

    option = f"{parameter} {project_source_directory.as_posix()}"

    for args in [
        f"{option} show --only main",
        f"show {option} --only main",
        f"show --only main {option}",
    ]:
        tester.execute(args)
        assert tester.status_code == 0

        stdout = tester.io.fetch_output()
        stderr = tester.io.fetch_error()

        assert error_string not in stderr
        assert error_string not in stdout

        assert "certifi" in stdout
        assert len(stdout.splitlines()) == 8
