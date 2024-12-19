#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Provide a generic class for basic reporter setup
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import pytz
from slugify import slugify
from validators import url as valid_uri
from urllib.parse import urlparse
from webiquette.webi import Webi


class ReporterWebWait(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class Reporter:
    def __init__(
        self,
        name: str,  # name of the reporter instance (e.g., pleiades-news-blog)
        api_base_uri: str,
        headers: dict,
        respect_robots_txt: bool,
        expire_after: timedelta,
        cache_control: bool,
        cache_dir_path: Path,
    ):
        self.name = slugify(name)
        self.api_base_uri = api_base_uri
        self.cache_dir_path = cache_dir_path
        if not name:
            raise ValueError(f"Reporter name cannot be an empty string: '{name}'")
        if not valid_uri(api_base_uri):
            raise ValueError(f"Invalid API Base Uri: '{api_base_uri}'")
        self._webi = Webi(
            netloc=urlparse(api_base_uri).netloc,
            headers=headers,
            respect_robots_txt=respect_robots_txt,
            expire_after=expire_after,
            cache_control=cache_control,
            cache_dir=str(cache_dir_path),
        )
        self._last_web_request = datetime.fromisoformat("1900-01-01T12:12:12+00:00")
        self._wait_until = (
            self._last_web_request
        )  # do not make another request before this datetime
        self._wait_every_time = 0  # seconds to wait before each request
        self._cache_read()

    @property
    def last_check(self) -> datetime:
        return self._last_check

    @last_check.setter
    def last_check(self, val: datetime):
        self._last_check = val
        try:
            self._cache_write()
        except AttributeError:
            pass

    def _cache_read(self) -> dict:
        """
        Read critical info from this Reporter's local cache
        """
        cache_file_path = (
            self.cache_dir_path / f"{self.name.replace('-', '_')}_metadata.json"
        )
        if not cache_file_path.exists():
            self._cache_write()
        with open(
            self.cache_dir_path / cache_file_path,
            "r",
            encoding="utf-8",
        ) as f:
            cached_data = json.load(f)
        del f
        return cached_data

    def _cache_write(self, data_to_cache: dict):
        """
        Write critical data to this Reporter's local cache
        """
        self.cache_dir_path.mkdir(parents=True, exist_ok=True)
        cache_file_path = (
            self.cache_dir_path / f"{self.name.replace('-', '_')}_metadata.json"
        )
        with open(cache_file_path, "w", encoding="utf-8") as f:
            json.dump(data_to_cache, f)
        del f

    def _web_get(
        self,
        additional_headers: dict = dict(),
        bypass_cache: bool = False,
        retries: int = 1,
        backoff_step: int = 15,
        **kwargs,
    ):
        now = datetime.now(tz=pytz.utc)
        wait_until = max(
            self._wait_until,
            self._last_web_request + timedelta(seconds=self._wait_every_time),
        )
        if wait_until > now:
            raise ReporterWebWait(self._wait_until)
        r = self._webi.get(
            uri=self.api_base_uri,
            additional_headers=additional_headers,
            bypass_cache=bypass_cache,
            retries=retries,
            backoff_step=backoff_step,
            **kwargs,
        )
        now = datetime.now(tz=pytz.utc)
        self._last_web_request = now
        return r
