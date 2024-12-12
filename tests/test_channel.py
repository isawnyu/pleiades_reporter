#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the channel module
"""

from pleiades_reporter.channel import Channel
from pytest import raises


class TestChannel:
    @classmethod
    def setup_class(cls):
        cls.c = Channel()
        cls.test_posts = "fee fi fo fum".split()

    def test_init(self):
        assert len(self.c.queue) == 0

    def test_clear(self):
        self.c.enqueue(self.test_posts)
        self.c.clear()
        assert len(self.c.queue) == 0

    def test_enqueue(self):
        self.c.enqueue(self.test_posts)
        assert len(self.c.queue) == 4
        self.c.clear()

    def test_enqueue_more(self):
        self.c.enqueue(self.test_posts)
        self.c.enqueue(["foo"])
        assert len(self.c.queue) == 5
        self.c.clear()

    def test_enqueue_bad(self):
        with raises(TypeError):
            self.c.enqueue("foobar")
        self.c.clear()

    def test_enqueue_first(self):
        self.c.enqueue(self.test_posts)
        self.c.enqueue(["foo"], first=True)
        assert self.c.queue[0] == "foo"
        self.c.clear()

    def test_enqueue_last(self):
        self.c.enqueue(self.test_posts)
        self.c.enqueue(["foo"], first=False)
        assert self.c.queue[-1] == "foo"
        self.c.clear()

    def test_post_next(self):
        self.c.enqueue(self.test_posts)
        self.c.post_next()
        assert len(self.c.queue) == 3
        self.c.clear()

    def test_post(self):
        self.c.enqueue(self.test_posts)
        self.c.post_now("foo")
        assert len(self.c.queue) == 4
        self.c.clear()
