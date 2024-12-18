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
from pathlib import Path
import pickle
from slugify import slugify


class Channel:
    def __init__(self, name: str, cache_dir_path: Path):
        self.name = slugify(name)
        self.cache_dir_path = cache_dir_path
        self.queue = deque()
        if self.logger is None:
            self.logger = getLogger("Channel")
        self._cache_read()

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
            self._cache_write()
            c = len(results)
            self.logger.info(
                f"Posted {c} report{("", "s")[c>1]}. Items still in queue: {len(self.queue)}."
            )
        else:
            self.logger.info(f"Queue is empty; nothing to post.")

    def post_now(self, post):
        """Post this post immediately."""
        result = self._post(post)

    def _cache_read(self):
        fn = self.cache_dir_path / (self.name + "_queue.pickle")
        if not fn.exists():
            self._cache_write()
        with open(self.cache_dir_path / fn, "rb") as f:
            self.queue = pickle.load(f)
        del f

    def _cache_write(self):
        fn = self.cache_dir_path / (self.name + "_queue.pickle")
        with open(self.cache_dir_path / fn, "wb") as f:
            pickle.dump(self.queue, f)
        del f

    def _post(self, post):
        """Override this method in subclass to handle specific channel API"""
        pass
