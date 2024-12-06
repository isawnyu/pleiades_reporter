#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Define a standard report object
"""
from pleiades_reporter.text import norm


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
    """

    def __init__(self, **kwargs):
        self._title = ""
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, s: str):
        self._title = norm(s)
