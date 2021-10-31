from poetry.sources.links import HTMLPageLinkPackageSource


class SimpleRepositoryPage(HTMLPageLinkPackageSource):
    def __init__(self, url: str, content: str) -> None:
        if not url.endswith("/"):
            url += "/"
        super().__init__(url=url, content=content)
