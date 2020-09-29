import os

from typing import Union

from poetry.exceptions import PoetryException
from poetry.utils._compat import PY2
from poetry.utils._compat import Path
from poetry.utils.env import Env
from poetry.utils.env import ephemeral_environment


def pip_install(
    path, environment, editable=False, deps=False, upgrade=False
):  # type: (Union[Path, str], Env, bool, bool, bool) -> None
    path = Path(path) if isinstance(path, str) else path

    args = ["install", "--prefix", str(environment.path)]

    if upgrade:
        args.append("--upgrade")

    if not deps:
        args.append("--no-deps")

    if editable:
        if not path.is_dir():
            raise PoetryException(
                "Cannot install non directory dependencies in editable mode"
            )
        args.append("-e")

    args.append(str(path))

    if path.is_file() and path.suffix == ".whl":
        return environment.run_pip(*args)

    with ephemeral_environment(
        executable=environment.python, pip=True, setuptools=True
    ) as env:
        return env.run(
            "pip",
            *args,
            env=dict(os.environ, PYTHONPATH=str(environment.purelib)) if PY2 else None
        )


def pip_editable_install(directory, environment):  # type: (Path, Env) -> None
    return pip_install(
        path=directory, environment=environment, editable=True, deps=False, upgrade=True
    )
