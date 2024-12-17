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
from pleiades_reporter.pleiades import PleiadesBlogReporter, PleiadesRSSReporter
import pytz


class TestPleiadesRSSReporter:
    @classmethod
    def setup_class(cls):
        cls.r = PleiadesRSSReporter(
            name="pleiades-new-places",
            api_base_uri="https://pleiades.stoa.org/indexes/published/RSS",
            user_agent="PleiadesReporter/0.1 (+https://pleiades.stoa.org)",
            from_header="pleiades.admin@nyu.edu",
        )

    def test_extra(self):
        pid = "89105"
        j = self.r._get_pleiades_json(f"https://pleiades.stoa.org/places/{pid}")
        s = self.r._get_modification_summary(
            j, cutoff_date=datetime(year=2024, month=12, day=15, tzinfo=pytz.utc)
        )
        assert s != ""
