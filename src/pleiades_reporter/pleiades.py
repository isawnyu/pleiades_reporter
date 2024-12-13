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
import json
from pathlib import Path
from platformdirs import user_cache_dir
from pleiades_reporter.atom import AtomReporter
from pleiades_reporter.reporter import Reporter
import pytz

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

    def check(self):
        """
        Check for new Pleiades records since last check and return a list of reports
        """
        now = datetime.now(tz=pytz.utc)
        if self._wait_until > now:
            return list()
        if self._wait_every_time:
            if self._last_web_request + timedelta(seconds=self._wait_every_time) > now:
                return list()
        new_records = self._get_new_pleiades_records(bypass_cache=True)
        self.logger.debug(f"Got {len(new_records)}")
        return [self._make_report(rec) for rec in new_records]

    def _cache_read(self):
        """
        Read critical info from the local cache
        - last datetime checked
        """
        try:
            with open(
                CACHE_DIR_PATH / "zotero_metadata.json", "r", encoding="utf-8"
            ) as f:
                d = json.load(f)
            del f
        except FileNotFoundError:
            # write a version and date that will ensure updates must be checked
            self._last_zot_version = "38632"
            self._last_check = datetime.fromisoformat("2024-01-01T12:12:12+00:00")
            self._zot_cache_write()
        else:
            self._last_zot_version = d["last_version_checked"]
            self._last_check = datetime.fromisoformat(d["last_time_checked"])

    def _cache_write(self):
        """
        Write critical info to the local cache
        - last datetime checked
        """
        d = {
            "last_version_checked": self._last_zot_version,
            "last_time_checked": self._last_check.isoformat(),
        }
        with open(CACHE_DIR_PATH / "zotero_metadata.json", "w", encoding="utf-8") as f:
            json.dump(d, f)
        del f
