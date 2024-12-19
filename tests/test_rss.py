#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_reporter.rss module
"""

import logging
from pathlib import Path
from pleiades_reporter.rss import BetterRSSHandler
from pprint import pformat
import shutil
from webiquette.webi import Webi

test_cache_dir = Path("tests/data/webcache/").resolve()
feed_url = (
    "https://pleiades.stoa.org/indexes/published-places-names-locations-connections/RSS"
)


class TestBetterRSSHander:
    @classmethod
    def setup_class(cls):
        cls.h = BetterRSSHandler(
            cache_path=test_cache_dir, name="test_better_rss_handler"
        )
        test_cache_dir.mkdir(parents=True, exist_ok=True)
        cls.w = Webi(
            netloc="pleiades.stoa.org",
            headers={
                "User-Agent": "PleiadesReporterTester/0.1 (+https://pleiades.stoa.org)",
                "from": "pleiades.admin@nyu.edu",
            },
            respect_robots_txt=False,
            cache_control=False,
            cache_dir=str(test_cache_dir),
        )

    @classmethod
    def teardown_class(cls):
        del cls.w
        del cls.h
        shutil.rmtree(test_cache_dir)

    def test_fetch_nofilter(self):
        dated_entries = self.h._fetch(
            feed_url=feed_url, web_interface=self.w, filter=False
        )
        # logger = logging.getLogger(
        #     "::".join((Path(__file__).name, "TestBetterRSSHandler", "test_fetch"))
        # )
        assert isinstance(dated_entries, list)

    def test_fetch_filtered(self):
        dated_entries = self.h._fetch(
            feed_url=feed_url, web_interface=self.w, filter=False
        )
        orig_len = len(dated_entries)
        if orig_len > 1:
            self.h.reset()
            self.h._rss_seen = {e.guid: dt_iso for e, dt_iso in dated_entries[1:]}
            sought_guids = [e.guid for e, dt_iso in dated_entries[0:2]]
            new_entries = self.h._fetch(
                feed_url=feed_url, web_interface=self.w, filter=True
            )
            new_guids = {e.guid for e, dt_iso in new_entries}
            assert sought_guids[0] in new_guids
            assert sought_guids[1] not in new_guids
