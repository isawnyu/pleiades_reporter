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
from pleiades_reporter.report import PleiadesReport
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
        # get new feed entries that have update dates since our last check
        new_places = list()
        new_records = self._get_new_entries(since=self.last_check)
        self.logger.debug(
            f"Got {len(new_records)} feed records updated since {self.last_check.isoformat()}"
        )
        this_check = datetime.now(tz=pytz.utc)
        if new_records:
            pleiades_json = [self._get_pleiades_json(r.link) for r in new_records]
            self.logger.debug(
                f"Got {len(pleiades_json)} json files from Pleiades {this_check.isoformat()}"
            )
            pleiades_creates = [
                datetime.fromisoformat(j["history"][-1]["modified"])
                for j in pleiades_json
            ]
            new_places = [
                pleiades_json[i]
                for i, dt in enumerate(pleiades_creates)
                if dt >= self.last_check
            ]
            self.logger.debug(f"Got {len(new_places)} new indexes")
        self.last_check = this_check
        return [self._make_report(place) for place in new_places]

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

    def _get_pleiades_json(self, puri: str):
        juri = puri + "/json"
        r = self._webi.get(uri=juri)
        if r.status_code == 200:
            return r.json()
        r.raise_for_status

    def _make_report(self, place: dict) -> PleiadesReport:
        raise NotImplementedError()


class PleiadesAtomReporter:
    pass
