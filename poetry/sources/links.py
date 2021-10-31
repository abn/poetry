import re
import urllib.parse
import warnings

from abc import abstractmethod
from html import unescape
from typing import Iterator
from typing import Optional
from typing import Tuple

from poetry.core.packages.utils.link import Link
from poetry.core.semver.version import Version
from poetry.utils.helpers import canonicalize_name
from poetry.utils.patterns import wheel_file_re


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import html5lib


class LinkPackageSource:
    VERSION_REGEX = re.compile(r"(?i)([a-z0-9_\-.]+?)-(?=\d)([a-z0-9_.!+-]+)")
    CLEAN_REGEX = re.compile(r"[^a-z0-9$&+,/:;=?@.#%_\\|-]", re.I)
    SUPPORTED_FORMATS = [
        ".tar.gz",
        ".whl",
        ".zip",
        ".tar.bz2",
        ".tar.xz",
        ".tar.Z",
        ".tar",
    ]

    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def url(self):
        return self._url

    @property
    def versions(self) -> Iterator[Version]:
        seen = set()
        for link in self.links:
            version = self.link_version(link)

            if not version:
                continue

            if version in seen:
                continue

            seen.add(version)

            yield version

    @property
    def packages(self) -> Iterator[Tuple[str, Version, Link]]:
        seen = set()
        for link in self.links:
            name, version = self.link_package_data(link)

            if not name or not version:
                continue

            if (name, version) in seen:
                continue

            seen.add((name, version, link))

            yield name, version, link

    @property
    @abstractmethod
    def links(self) -> Iterator[Link]:
        raise

    def link_package_data(self, link: Link) -> Tuple[Optional[str], Optional[Version]]:
        name, version = None, None
        m = wheel_file_re.match(link.filename)
        if m:
            name = canonicalize_name(m.group("name"))
            version = m.group("ver")
        else:
            info, ext = link.splitext()
            match = self.VERSION_REGEX.match(info)
            if match:
                version = match.group(2)

        try:
            version = Version.parse(version)
        except ValueError:
            pass

        return name, version

    def links_for_package(self, name: str, version: Version) -> Iterator[Link]:
        name = canonicalize_name(name)

        for link in self.links:
            if self.link_package_data(link) == (name, version):
                yield link

    def links_for_version(self, version: Version) -> Iterator[Link]:
        for link in self.links:
            if self.link_version(link) == version:
                yield link

    def link_version(self, link: Link) -> Optional[Version]:
        return self.link_package_data(link)[1]

    def clean_link(self, url: str) -> str:
        """Makes sure a link is fully encoded.  That is, if a ' ' shows up in
        the link, it will be rewritten to %20 (while not over-quoting
        % or other characters)."""
        return self.CLEAN_REGEX.sub(lambda match: "%%%2x" % ord(match.group(0)), url)


class HTMLPageLinkPackageSource(LinkPackageSource):
    def __init__(self, url: str, content: str) -> None:
        super().__init__(url=url)

        self._content = content
        self._parsed = html5lib.parse(content, namespaceHTMLElements=False)
        # if encoding is None:
        #     self._parsed = html5lib.parse(content, namespaceHTMLElements=False)
        # else:
        #     self._parsed = html5lib.parse(
        #         content, transport_encoding=encoding, namespaceHTMLElements=False
        #     )

    @property
    def links(self) -> Iterator[Link]:
        for anchor in self._parsed.findall(".//a"):
            if anchor.get("href"):
                href = anchor.get("href")
                url = self.clean_link(urllib.parse.urljoin(self._url, href))
                pyrequire = anchor.get("data-requires-python")
                pyrequire = unescape(pyrequire) if pyrequire else None
                link = Link(url, self, requires_python=pyrequire)

                if link.ext not in self.SUPPORTED_FORMATS:
                    continue

                yield link
