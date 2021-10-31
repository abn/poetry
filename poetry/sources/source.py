import logging

from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import List
from typing import Optional
from typing import Tuple

from poetry.core.semver.helpers import VersionTypes
from poetry.core.semver.helpers import parse_constraint
from poetry.core.semver.version_constraint import VersionConstraint
from poetry.core.semver.version_range import VersionRange


if TYPE_CHECKING:
    from poetry.core.packages.dependency import Dependency
    from poetry.core.packages.package import Package
    from poetry.core.packages.utils.link import Link


class PackageSource:
    def __init__(self, name: str) -> None:
        self._name = name
        self._packages = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def packages(self) -> List["Package"]:
        return self._packages

    @abstractmethod
    def find_packages(self, dependency: "Dependency") -> None:
        raise NotImplementedError()

    def has_package(self, package: "Package") -> bool:
        package_id = package.unique_name

        for repo_package in self.packages:
            if package_id == repo_package.unique_name:
                return True

        return False

    def add_package(self, package: "Package") -> None:
        self._packages.append(package)

    def remove_package(self, package: "Package") -> None:
        package_id = package.unique_name

        index = None
        for i, repo_package in enumerate(self.packages):
            if package_id == repo_package.unique_name:
                index = i
                break

        if index is not None:
            del self._packages[index]

    def search(self, query: str) -> List["Package"]:
        results = []

        for package in self.packages:
            if query in package.name:
                results.append(package)

        return results

    @staticmethod
    def _get_constraints_from_dependency(
        dependency: "Dependency",
    ) -> Tuple[VersionTypes, bool]:
        constraint = dependency.constraint
        if constraint is None:
            constraint = "*"

        if not isinstance(constraint, VersionConstraint):
            constraint = parse_constraint(constraint)

        allow_prereleases = dependency.allows_prereleases()
        if isinstance(constraint, VersionRange):
            if (
                constraint.max is not None
                and constraint.max.is_unstable()
                or constraint.min is not None
                and constraint.min.is_unstable()
            ):
                allow_prereleases = True

        return constraint, allow_prereleases

    def _log(self, msg: str, level: str = "info") -> None:
        getattr(logging.getLogger(self.__class__.__name__), level)(
            f"<debug>{self.name}:</debug> {msg}"
        )

    def __len__(self) -> int:
        return len(self._packages)

    def find_links_for_package(self, package: "Package") -> List["Link"]:
        return []

    def package(
        self, name: str, version: str, extras: Optional[List[str]] = None
    ) -> "Package":
        name = name.lower()

        for package in self.packages:
            if name == package.name and package.version.text == version:
                return package.clone()
