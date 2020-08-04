# -*- coding: utf-8 -*-

from poetry.utils._compat import Path

from .layout import Layout


class SrcLayout(Layout):
    @property
    def basedir(self):  # type: () -> Path
        return Path("src")
