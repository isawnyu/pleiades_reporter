#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Define a standard report object
"""
from datetime import datetime
import pytz
import logging
from mdclense.parser import MarkdownParser
from pleiades_reporter.text import norm

mdparser = MarkdownParser()


class PleiadesReport:
    """
    Standard report objects
    Capabilities:
    - title
    - summary
    - plain text version
    - markdown version
    - hash tags
    - associated images and alt text
    - when (date of the reported change/event)
    """

    def __init__(self, **kwargs):
        self._title = ""
        self._summary = ""
        self._text = ""
        self._markdown = ""
        self._when = datetime.now(tz=pytz.utc)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, s: str):
        self._title = norm(s)

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, s: str):
        self._summary = norm(s)

    @property
    def text(self):
        if self._text:
            return self._text
        elif self._markdown:
            return norm(mdparser.parse(self._markdown), preserve=["\n"])
        else:
            return ""

    @text.setter
    def text(self, s: str):
        self._text = norm(s)

    @property
    def markdown(self):
        return self._markdown

    @markdown.setter
    def markdown(self, s: str):
        logger = logging.getLogger("markdown")
        logger.debug(f"s: '{s}'")
        s_clean = norm(s, preserve=["\n"], trim=False)
        logger.debug(f"norm(s): '{s_clean}'")
        while s_clean[0] == "\n":
            s_clean = s_clean[1:]
        while s_clean[-1] == "\n":
            s_clean = s_clean[:-1]
        logger.debug(f"s_clean final: '{s_clean}'")
        self._markdown = s_clean

    @property
    def when(self):
        return self._when

    @when.setter
    def when(self, dt: datetime | str):
        if isinstance(dt, datetime):
            self._when = dt
        elif isinstance(dt, str):
            self._when = datetime.fromisoformat(dt)
        else:
            raise TypeError(f"Expected datetime or str, got {type(dt)}")

    def __str__(self):
        return self.text
