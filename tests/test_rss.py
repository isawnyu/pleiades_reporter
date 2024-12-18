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
        cls.h = BetterRSSHandler()
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
        entries = self.h._fetch(feed_url=feed_url, web_interface=self.w, filter=False)
        # logger = logging.getLogger(
        #     "::".join((Path(__file__).name, "TestBetterRSSHandler", "test_fetch"))
        # )
        assert isinstance(entries, list)

    def test_fetch_filtered(self):
        entries = self.h._fetch(feed_url=feed_url, web_interface=self.w, filter=False)
        orig_len = len(entries)
        if orig_len > 0:
            self.h.reset()
            self.h._rss_seen_hashes = {self.h._hash_entry(e) for e in entries[1:]}
        sought_hashes = (self.h._hash_entry(entries[0]), self.h._hash_entry(entries[1]))
        new_entries = self.h._fetch(
            feed_url=feed_url, web_interface=self.w, filter=True
        )
        new_hashes = {self.h._hash_entry(e) for e in new_entries}
        assert sought_hashes[0] in new_hashes
        assert sought_hashes[1] not in new_hashes
