#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the channel module
"""

from pleiades_reporter.channel import Channel


class TestChannel:

    def test_init(self):
        c = Channel()
