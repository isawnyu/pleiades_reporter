#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Report on activity in the Pleaides Zotero Library
"""
from pleiades_reporter.report import PleiadesReport


class ZoteroReporter:
    """
    Capabilities:
    - Get new bibliographic items since a previous version and produce a list of corresponding PleiadesReport objects, one
      per new item.
    """

    def __init__(self):
        pass
