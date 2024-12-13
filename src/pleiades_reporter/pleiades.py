#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Subclass AtomReporter to deal with Pleiades AtomFeeds
"""
from datetime import timedelta
from pathlib import Path
from platformdirs import user_cache_dir
from pleiades_reporter.atom import AtomReporter
from pleiades_reporter.reporter import Reporter

CACHE_DIR_PATH = Path(user_cache_dir("pleiades_reporter"))

HEADERS = dict()
WEB_CACHE_DURATION = 157  # minutes


class PleiadesAtomReporter(Reporter, AtomReporter):
    def __init__(self, api_base_uri: str, user_agent: str, from_header: str):
        headers = HEADERS
        headers["User-Agent"] = user_agent
        headers["From"] = from_header
        Reporter.__init__(
            self,
            api_base_uri=api_base_uri,
            headers=headers,
            respect_robots_txt=False,
            expire_after=timedelta(minutes=WEB_CACHE_DURATION),
            cache_control=False,
            cache_dir_path=CACHE_DIR_PATH,
        )
        AtomReporter.__init__(self)
