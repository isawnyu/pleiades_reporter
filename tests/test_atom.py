#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_reporter.atom module
"""

from pleiades_reporter.atom import AtomReporter
import pytz


class TestAtomReporter:
    @classmethod
    def setup_class(cls):
        cls.r = AtomReporter()

    def test_init(self):
        assert isinstance(self.r, AtomReporter)
