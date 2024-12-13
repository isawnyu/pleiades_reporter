#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Subclass AtomReporter to deal with Pleiades AtomFeeds
"""
from datetime import datetime, timedelta
from logging import getLogger
from pathlib import Path
from platformdirs import user_cache_dir
from pleiades_reporter.rss import RSSReporter
from pleiades_reporter.reporter import Reporter
import pytz

CACHE_DIR_PATH = Path(user_cache_dir("pleiades_reporter"))

HEADERS = dict()
WEB_CACHE_DURATION = 157  # minutes


class PleiadesRSSReporter(Reporter, RSSReporter):
    def __init__(self, name: str, api_base_uri: str, user_agent: str, from_header: str):
        headers = HEADERS
        headers["User-Agent"] = user_agent
        headers["From"] = from_header
        Reporter.__init__(
            self,
            name=name,
            api_base_uri=api_base_uri,
            headers=headers,
            respect_robots_txt=False,
            expire_after=timedelta(minutes=WEB_CACHE_DURATION),
            cache_control=False,
            cache_dir_path=CACHE_DIR_PATH,
        )
        RSSReporter.__init__(self)
        self.logger = getLogger(f"pleiades.PleiadesRSSReporter({name})")

    def check(self):
        """
        Check for new Pleiades records since last check and return a list of reports
        """
        new_records = self._get_new_entries(since=self.last_check)
        self.logger.debug(f"Got {len(new_records)}")
        self.last_check = datetime.now(tz=pytz.utc)
        return [self._make_report(rec) for rec in new_records]

    def _cache_read(self):
        """
        Read critical Pleiades info from the local cache
        - last datetime checked
        """
        try:
            cached_data = Reporter._cache_read(self)
        except FileNotFoundError:
            # write a date that will ensure updates must be checked
            self._last_check = datetime.fromisoformat("2024-01-01T12:12:12+00:00")
            self._cache_write()
        else:
            self._last_check = datetime.fromisoformat(cached_data["last_time_checked"])

    def _cache_write(self):
        """
        Write critical Pleiades info to the local cache
        - last datetime checked
        """
        d = {
            "last_time_checked": self._last_check.isoformat(),
        }
        Reporter._cache_write(self, d)


class PleiadesAtomReporter:
    pass
