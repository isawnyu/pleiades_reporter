#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the go_to_social module
"""

from pleiades_reporter.go_to_social import GoToSocialChannel
from pytest import raises


class TestGoToSocial:
    @classmethod
    def setup_class(cls):
        cls.c = GoToSocialChannel()

    def test_init(self):
        assert isinstance(self.c, GoToSocialChannel)
