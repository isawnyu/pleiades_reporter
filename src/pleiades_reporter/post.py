#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Define a Post class
"""


class Post:
    def __init__(self, body: str = "", tags: list = list()):
        self.body = body
        self.tags = tags
