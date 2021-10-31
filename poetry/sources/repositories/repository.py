from typing import TYPE_CHECKING
from typing import List

from poetry.sources.source import PackageSource


if TYPE_CHECKING:
    from poetry.core.packages.dependency import Dependency
    from poetry.core.packages.package import Package


class Repository(PackageSource):
    def __init__(self, packages: List["Package"] = None, name: str = None) -> None:
        super().__init__(name)

        if packages is None:
            packages = []

        for package in packages:
            self.add_package(package)

    def find_packages(self, dependency: "Dependency") -> List["Package"]:
        packages = []
        ignored_pre_release_packages = []
        constraint, allow_prereleases = self._get_constraints_from_dependency(
            dependency
        )

        for package in self.packages:
            if dependency.name == package.name:
                if (
                    package.is_prerelease()
                    and not allow_prereleases
                    and not package.source_type
                ):
                    # If prereleases are not allowed and the package is a prerelease
                    # and is a standard package then we skip it
                    if constraint.is_any():
                        # we need this when all versions of the package are pre-releases
                        ignored_pre_release_packages.append(package)
                    continue

                if constraint.allows(package.version) or (
                    package.is_prerelease()
                    and constraint.allows(package.version.next_patch())
                ):
                    packages.append(package)

        return packages or ignored_pre_release_packages
