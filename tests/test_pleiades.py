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
from pleiades_reporter.pleiades import PleiadesReporter


class TestPleiadesReporter:
    @classmethod
    def setup_class(cls):
        cls.r = PleiadesReporter()
