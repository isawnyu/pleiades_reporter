#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_reporter.pleiades module
"""

from datetime import datetime
from pathlib import Path
from pleiades_reporter.pleiades import (
    PleiadesBlogReporter,
    PleiadesRSSReporter,
    PleiadesChangesReporter,
)
import pytz
import shutil

USER_AGENT = "PleiadesReporterTester/0.1 (+https://pleiades.stoa.org)"
FROM_EMAIL = "pleiades.admin@nyu.edu"
test_cache_dir = Path("tests/data/webcache/").resolve()


class TestPleiadesRSSReporter:
    @classmethod
    def setup_class(cls):
        cls.r = PleiadesRSSReporter(
            name="pleiades-new-places",
            api_base_uri="https://pleiades.stoa.org/indexes/published/RSS",
            user_agent=USER_AGENT,
            from_header=FROM_EMAIL,
        )

    def test_extra(self):
        pid = "89105"
        j = self.r._get_pleiades_json(f"https://pleiades.stoa.org/places/{pid}")
        s = self.r._get_modification_summary(
            j, cutoff_date=datetime(year=2024, month=12, day=15, tzinfo=pytz.utc)
        )
        assert s != ""


class TestPleiadesChangesReporter:
    @classmethod
    def setup_class(cls):
        cls.r = PleiadesChangesReporter(
            name="test_pleiades_changes_reporter",
            api_base_uri="https://pleiades.stoa.org/indexes/published-places-names-locations-connections/RSS",
            user_agent=USER_AGENT,
            from_header=FROM_EMAIL,
            cache_dir_path=test_cache_dir,
        )

    @classmethod
    def teardown_class(cls):
        del cls.r
        shutil.rmtree(test_cache_dir, ignore_errors=True)

    def test_check(self):
        result = self.r.check()
        assert isinstance(result, list)
