#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Provide a generic class for reporting on content in RSS feeds
"""
from datetime import datetime, timezone, timedelta
import feedparser
import itertools
import json
from pathlib import Path
from pleiades_reporter.reporter import ReporterWebWait
import pytz
from time import struct_time


class JSONDecoderSeen(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        ret = {}
        for key, value in obj.items():
            ret[key] = datetime.fromisoformat(value)
        return ret


class JSONEncoderSeen(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(obj)


class RSSReporter:
    def __init__(self, cache_dir_path: Path, **kwargs):
        self.seen_in_feed = dict()
        self.cache_dir_path = cache_dir_path
        RSSReporter._cache_seen_read(self)

    def _get_latest_entries(self, bypass_cache: bool = True) -> list:
        """
        Get new entries in the feed since since_datetime and return them as a list
        """
        try:
            r = self._web_get(
                bypass_cache=bypass_cache,
            )
        except ReporterWebWait:
            # request delay rules indicate we cannot make the request yet, so move on
            return list()
        if r.status_code != 200:
            r.raise_for_status()
        else:
            d = feedparser.parse(r.text)
            guids = {e.guid: self._dt_from_tstruct(e.updated_parsed) for e in d.entries}
            new_guids = dict()
            for guid, dt in guids.items():
                try:
                    last_seen = self.seen_in_feed[guid]
                except KeyError:
                    new_guids[guid] = dt
                else:
                    if last_seen < dt:
                        new_guids[guid] = dt
            for guid, dt in new_guids.items():
                self.seen_in_feed[guid] = dt
            RSSReporter._cache_seen_write(self)
            return [e for e in d.entries if e.guid in new_guids.keys()]

    def _dt_from_tstruct(self, ts: struct_time) -> datetime:
        """
        Nadia Alramli with Sam Mason
        https://stackoverflow.com/questions/1697815/how-do-you-convert-a-time-struct-time-object-into-a-datetime-object#answer-1697838
        """
        tz = None
        if ts.tm_gmtoff is not None:
            tz = timezone(timedelta(seconds=ts.tm_gmtoff))
        else:
            tz = pytz.utc
        if ts.tm_sec in {60, 61}:
            return datetime(*ts[:5], 59, tzinfo=tz)
        return datetime(*ts[:6], tzinfo=tz)

    def _cache_seen_read(self):
        """
        Read critical info from this Reporter's local cache
        """
        fn = self.cache_dir_path / f"{self.name.replace('-', '_')}_rss_seen.json"
        if not fn.exists():
            RSSReporter._cache_seen_write(self)
        with open(
            fn,
            "r",
            encoding="utf-8",
        ) as f:
            cached_data = json.load(f, cls=JSONDecoderSeen)
        del f
        self.seen_in_feed = cached_data

    def _cache_seen_write(self):
        """
        Write critical data to this Reporter's local cache
        """
        sorted_seen = {
            k: v
            for k, v in sorted(
                self.seen_in_feed.items(), key=lambda item: item, reverse=True
            )
        }
        max_cached = max(500, len(sorted_seen))
        recently_seen = dict(itertools.islice(sorted_seen.items(), max_cached))
        fn = self.cache_dir_path / f"{self.name.replace('-', '_')}_rss_seen.json"
        with open(
            fn,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(recently_seen, f, cls=JSONEncoderSeen)
        del f
