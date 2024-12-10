#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the report module
"""

from pleiades_reporter.report import PleiadesReport


class TestPleiadesReport:
    def test_init_title(self):
        t = "Annales ab excessu divi Augusti"
        r = PleiadesReport(title=t)
        assert r.title == t

    def test_change_title(self):
        t = "Annales ab excessu divi Augusti"
        r = PleiadesReport(title=t)
        assert r.title == t
        t = "Academicorum reliquiae cum Lucullo"
        r.title = t
        assert r.title == t

    def test_init_summary(self):
        s = "Eum voluptatem illum sit minus."
        r = PleiadesReport(summary=s)
        assert r.summary == s

    def test_change_summary(self):
        s = "Eum voluptatem illum sit minus."
        r = PleiadesReport(summary=s)
        assert r.summary == s
        s = "Aspernatur id molestias deleniti eius quis qui corporis veritatis."
        r.summary = s
        assert r.summary == s
