#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_reporter.reporter module
"""

from pleiades_reporter.reporter import Reporter
import pytz


class TestReporter:
    @classmethod
    def setup_class(cls):
        cls.r = Reporter()

    def test_init(self):
        assert isinstance(self.r, Reporter)
