#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_reporter.pleiades module
"""

from datetime import datetime, date
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

    def test_filter_histories(self):
        pjson = self.r._get_place_json("http://pleiades.stoa.org/places/471134383")
        histories = self.r._get_histories(pjson)
        filtered_histories = self.r._filter_histories(histories, "2024-12-01T05:10:15Z")
        import logging
        from pprint import pformat

        logger = logging.getLogger("test_filter_histories")
        logger.error(pformat(filtered_histories))

    def test_filter_histories_2(self):
        pjson = self.r._get_place_json("https://pleiades.stoa.org/places/89124")
        histories = self.r._get_histories(pjson)
        filtered_histories = self.r._filter_histories(histories, "2024-12-01T05:10:15Z")
        import logging
        from pprint import pformat

        logger = logging.getLogger("test_filter_histories")
        logger.error(pformat(filtered_histories))

    def test_filter_history(self):
        raw_history = [
            {
                "comment": "Edited type for fort; update references @maximeg",
                "modifiedBy": "jbecker",
                "modified": "2024-12-17T02:10:59Z",
            },
            {
                "comment": "Baseline created",
                "modifiedBy": "maximeg",
                "modified": "2024-12-17T00:31:09Z",
            },
            {
                "comment": "DARMC 19068",
                "modifiedBy": "jbecker",
                "modified": "2018-08-09T23:38:19Z",
            },
            {
                "comment": "added references",
                "modifiedBy": "jbecker",
                "modified": "2015-11-16T19:07:27Z",
            },
            {
                "comment": "fixing connection directions",
                "modifiedBy": "thomase",
                "modified": "2013-06-21T20:10:40Z",
            },
            {
                "comment": "Location updates and tags from Johan Ahlfeldt's (jahlfeldt) Digital Atlas of the Roman Empire in October 2012",
                "modifiedBy": "sgillies",
                "modified": "2012-10-20T23:59:53Z",
            },
            {
                "comment": "improved in all ways",
                "modifiedBy": "thomase",
                "modified": "2012-07-09T17:20:25Z",
            },
            {
                "comment": "Global migration and reindexing of citations and provenance, February 2012",
                "modifiedBy": "admin",
                "modified": "2012-02-15T09:16:49Z",
            },
            {
                "comment": "Baseline created",
                "modifiedBy": "sarcanon",
                "modified": "2011-11-23T22:56:22Z",
            },
            {
                "comment": "New locations, coordinates, and metadata from Harvard's DARMC project. See http://atlantides.org/trac/pleiades/wiki/PlaceUpgradesAndMigrations",
                "modifiedBy": "sgillies",
                "modified": "2011-01-21T05:43:29Z",
            },
            {
                "comment": "Detail text updated from former modernLocation. See http://atlantides.org/trac/pleiades/wiki/PlaceDetailsUpgrade",
                "modifiedBy": "sgillies",
                "modified": "2011-01-14T21:25:48Z",
            },
            {
                "action": "Publish externally",
                "modifiedBy": "thomase",
                "modified": "2009-11-23T22:42:29Z",
            },
            {
                "action": "Submit for review",
                "modifiedBy": "sgillies",
                "modified": "2009-11-02T10:42:57Z",
            },
            {
                "action": "Create",
                "modifiedBy": "sgillies",
                "modified": "2009-11-02T09:54:08Z",
            },
        ]
        fh = self.r._filter_history(raw_history, date(year=2024, month=12, day=1))
        assert len(fh) == 2

    def test_get_histories(self):
        pjson = self.r._get_place_json("http://pleiades.stoa.org/places/471134383")
        histories = self.r._get_histories(pjson)
        keys = {"place", "locations", "names", "connections"}
        assert set(histories.keys()) == {"place", "locations", "names", "connections"}
        for k in keys:
            assert isinstance(histories[k], list)
            if k in {"locations", "connections"}:
                assert len(histories[k]) > 0

    def test_get_place_json(self):
        result = self.r._get_place_json("http://pleiades.stoa.org/places/471134383")
        assert result["id"] == "471134383"
