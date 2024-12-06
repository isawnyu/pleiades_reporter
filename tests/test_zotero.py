#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_reporter.zotero module
"""

from pleiades_reporter.zotero import ZoteroReporter


class TestZoteroReporter:
    @classmethod
    def setup_class(cls):
        cls.r = ZoteroReporter()

    def test_init(self):
        assert self.r._webi is not None
