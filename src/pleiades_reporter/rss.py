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
import logging
from pathlib import Path
from pleiades_reporter.dates import st2dt
from pleiades_reporter.reporter import ReporterWebWait
import pytz
from requests import Response
from time import struct_time
from validators import url as valid_url
from webiquette.webi import Webi


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


class BetterRSSHandler:

    def __init__(self, cache_path: Path, **kwargs):
        self.cache_path = cache_path
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.reset()

    def reset(self):
        self._rss_last_fetch = datetime(
            year=1970, month=1, day=1, hour=1, minute=11, second=0, tzinfo=pytz.utc
        )
        self._rss_seen = dict()
        self._rss_write_cache()

    @property
    def rss_last_fetch(self):
        return self._rss_last_fetch

    @rss_last_fetch.setter
    def rss_last_fetch(self, new_dt: datetime):
        self._rss_last_fetch = new_dt
        self._rss_write_cache()

    def _fetch(self, feed_url: str, web_interface: Webi, filter=True):
        """
        If the feed has changed on the server, fetch it anew (bypass local web caching)
        """
        dated_entries = list()
        additional_headers = {"If-modified-since": self.rss_last_fetch.isoformat()}
        r = web_interface.get(
            feed_url, additional_headers=additional_headers, bypass_cache=True
        )
        now = datetime.now(tz=pytz.utc)
        if r.status_code == 304:
            # server says "no modification"
            self.rss_last_fetch = now
        elif r.status_code == 200:
            # server says it has returned data
            self.rss_last_fetch = now
            feed_data = feedparser.parse(r.text)
            dated_entries = self._normalize_dates(feed_data.entries)
            if filter:
                dated_entries = self._filter_feed_entries(dated_entries)
            else:
                for e, dt_iso in dated_entries:
                    self._rss_seen[e.guid] = dt_iso
        else:
            r.raise_for_status()
        if dated_entries:
            self._rss_write_cache()
        return dated_entries

    def _filter_feed_entries(self, dated_entries: list) -> list:
        """
        Return a list of feed entries + ISO datetimes that we haven't seen before
        """
        new_entries_dated = list()
        for i, de in enumerate(dated_entries):
            e, dt_iso = de
            try:
                last_dt_iso = self._rss_seen[e.guid]
            except KeyError:
                new_entries_dated.append(dated_entries[i])
                self._rss_seen[e.guid] = dt_iso
            else:
                if dt_iso > last_dt_iso:
                    new_entries_dated.append(dated_entries[i])
                    self._rss_seen[e.guid] = dt_iso
        return new_entries_dated

    def _normalize_dates(self, entries: list) -> list:
        """
        Return a list of tuples: [(entry, ISO format datestring in UTC), ...] for each entry in entries
        The ISO format datestring uses whichever date is latest on the entry: updated or published
        """
        results = list()
        for e in entries:
            try:
                published = st2dt(e.published_parsed)
            except AttributeError:
                published = None
            try:
                updated = st2dt(e.updated_parsed)
            except AttributeError:
                updated = None
            latest_date = max([dt for dt in [published, updated] if dt is not None])
            results.append((e, latest_date.isoformat()))
        return results

    def _rss_read_cache(self):
        cache_fp = self.cache_path / "_".join((self.name, "_rss_cache.json"))
        with open(cache_fp, "r", encoding="utf-8") as f:
            d = json.load(f, cls=JSONDecoderSeen)
        del f
        self._rss_last_fetch = d["rss_last_fetch"]
        self._rss_seen = d["rss_seen"]

    def _rss_write_cache(self):
        d = {"rss_last_fetch": self._rss_last_fetch, "rss_seen": self._rss_seen}
        self.cache_path.mkdir(parents=True, exist_ok=True)
        cache_fp = self.cache_path / "_".join((self.name, "_rss_cache.json"))
        with open(cache_fp, "w", encoding="utf-8") as f:
            d = json.dump(d, f, cls=JSONEncoderSeen)
        del f
