#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Provide a generic class for reporting on content in RSS feeds
"""
from datetime import datetime
import feedparser
from pleiades_reporter.reporter import ReporterWebWait


class RSSReporter:
    def __init__(self, **kwargs):
        pass

    def _get_latest_entries(self, bypass_cache: bool = True) -> list:
        """
        Get new entries in the feed since since_datetime and return them as a list
        """
        try:
            r = self._web_get(
                bypass_cache=bypass_cache,
            )
        except ReporterWebWait:
            # request delay rules indicate we cannot make the request yet, so move on
            return list()
        if r.status_code != 200:
            r.raise_for_status()
        else:
            d = feedparser.parse(r.text)
            return d.entries
