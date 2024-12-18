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
from pathlib import Path
from platformdirs import user_cache_dir
from pleiades_reporter.channel import Channel
from pprint import pformat

CACHE_DIR_PATH = Path(user_cache_dir("pleiades_reporter"))


class GoToSocialChannel(Channel):
    def __init__(self, name, access_token, api_base_url, **kwargs):
        self.logger = getLogger("GoToSocialChannel")
        Channel.__init__(self, name=name, cache_dir_path=CACHE_DIR_PATH)
        self.api = Mastodon(
            access_token=access_token,
            api_base_url=api_base_url,
            version_check_mode="none",
            **kwargs,
        )

    def _serialize_post(self, post):
        content = post.body
        if post.tags:
            tags = " ".join([f"#{t}" for t in post.tags])
            content = "\n\n".join((post.body, tags))
        else:
            content = post.body
        return content

    def _post(self, post):
        result = self.api.status_post(
            status=self._serialize_post(post),
            language="en",
        )
        return result

    def preview(self, post):
        return self._serialize_post(post)
