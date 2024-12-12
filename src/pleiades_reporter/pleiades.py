#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Subclass AtomReporter to deal with Pleiades AtomFeeds
"""

from pleiades_reporter.atom import AtomReporter


class PleiadesAtomReporter(AtomReporter):
    def __init__(self):
        AtomReporter.__init__(self)
