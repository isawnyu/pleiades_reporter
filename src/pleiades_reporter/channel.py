#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Implement the Channel base class for queued dissemination channels
"""
from collections import deque
from logging import getLogger


class Channel:
    def __init__(self):
        self.queue = deque()
        if self.logger is None:
            self.logger = getLogger("Channel")

    def clear(self):
        """Remove all content from the queue"""
        self.queue.clear()

    def enqueue(self, posts: list, first: bool = False):
        """Add posts to the dissemination queue"""
        if not isinstance(posts, list):
            raise TypeError(
                f"Expected `posts` parameter to be of type list but got {type(posts)}."
            )
        if first:
            self.queue.extendleft(posts)
        else:
            self.queue.extend(posts)

    def post_next(self, count: int = 1):
        """Post the next `count` items in the queue"""
        results = list()
        for i in range(0, count):
            try:
                post = self.queue.pop()
            except IndexError:
                break  # queue is empty
            else:
                results.append(self._post(post))
        if results:
            c = len(results)
            self.logger.info(
                f"Posted {c} report{("", "s")[c>1]}. Items still in queue: {len(self.queue)}."
            )
        else:
            self.logger.info(f"Queue is empty; nothing to post.")

    def post_now(self, post):
        """Post this post immediately."""
        result = self._post(post)

    def _post(self, post):
        """Override this method in subclass to handle specific channel API"""
        pass
