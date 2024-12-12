#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the post module
"""

from pleiades_reporter.post import Post
from pytest import raises


class TestPost:
    @classmethod
    def setup_class(cls):
        cls.p = Post()

    def test_init(self):
        assert isinstance(self.p, Post)
