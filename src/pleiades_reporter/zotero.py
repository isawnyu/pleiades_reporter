#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Report on activity in the Pleaides Zotero Library
"""
from pleiades_reporter.report import PleiadesReport
from datetime import timedelta
from pathlib import Path
from platformdirs import user_cache_dir
from urllib.parse import urlparse
from webiquette.webi import Webi

API_BASE = "https://api.zotero.org"
HEADERS = {
    "User-Agent": "PleiadesReporter/0.1 (+https://pleiades.stoa.org)",
    "Zotero-API-Version": 3,
}
LIBRARY_ID = 2533


class ZoteroReporter:
    """
    Capabilities:
    - Get new bibliographic items since a previous version and produce a list of corresponding PleiadesReport objects, one
      per new item.
    """

    def __init__(
        self,
    ):
        self._webi = Webi(
            netloc=urlparse(API_BASE).netloc,
            headers=HEADERS,
            respect_robots_txt=False,
            expire_after=timedelta(minutes=7),
            cache_control=False,
            cache_dir=str(Path(user_cache_dir("pleiades_reporter"))),
        )
