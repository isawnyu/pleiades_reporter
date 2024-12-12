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


class Channel:
    def __init__(self):
        self.queue = deque()

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
        for i in range(0, count):
            try:
                post = self.queue.pop()
            except IndexError:
                break  # queue is empty
            else:
                self._post(post)

    def post_now(self, post):
        """Post this post immediately."""
        self._post(post)

    def _post(self, post):
        """Override this method in subclass to handle specific channel API"""
        pass
