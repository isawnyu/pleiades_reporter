#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Implement a class for interacting with a GoToSocial instance
"""
from logging import getLogger
from mastodon import Mastodon
from pleiades_reporter.channel import Channel
from pprint import pformat


class GoToSocialChannel(Channel):
    def __init__(self, access_token, api_base_url, **kwargs):
        self.logger = getLogger("GoToSocialChannel")
        Channel.__init__(self)
        self.api = Mastodon(
            access_token=access_token,
            api_base_url=api_base_url,
            version_check_mode="none",
            **kwargs,
        )

    def _post(self, post):
        result = self.api.status_post(
            status=post.body,
            language="en",
        )
        return result
