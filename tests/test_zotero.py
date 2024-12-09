#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_reporter.zotero module
"""

from datetime import datetime
from pleiades_reporter.zotero import ZoteroReporter
import pytz


class TestZoteroReporter:
    @classmethod
    def setup_class(cls):
        cls.r = ZoteroReporter()

    def test_init_webi(self):
        assert self.r._webi is not None

    def test_init_zot_version(self):
        assert self.r._last_zot_version is not None

    def test_init_last_datetime(self):
        assert isinstance(self.r._last_check, datetime)

    def test_check_latest_version_noref(self):
        new_version = self.r._check_for_latest_version(bypass_cache=True)
        assert str(int(new_version)) == new_version

    def test_check_latest_version(self):
        old_version = "38632"
        new_version = self.r._check_for_latest_version(
            bypass_cache=True, reference_zot_version=old_version
        )
        assert int(new_version) > int(old_version)

    def test_get_modified(self):
        old_version = "38632"
        modified = self.r._zot_get_modified_records(
            since_version=old_version, bypass_cache=True
        )
        assert len(modified) > 0

    def test_get_new(self):
        old_version = "38632"
        old_datetime = datetime(
            year=2024,
            month=12,
            day=6,
            hour=12,
            minute=12,
            second=12,
            tzinfo=pytz.utc,
        )
        new = self.r._zot_get_new_records(
            since_version=old_version, since_datetime=old_datetime, bypass_cache=True
        )
        assert len(new) > 0
