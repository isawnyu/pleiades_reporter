#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Report on activity in the Pleaides Zotero Library
"""
from pleiades_reporter.report import PleiadesReport
from pleiades_reporter.reporter import Reporter
from datetime import datetime, timedelta
import json
from logging import getLogger
from markdownify import markdownify
from os import environ
from pathlib import Path
from platformdirs import user_cache_dir
from pprint import pprint, pformat
import pytz
from requests import Response

API_BASE = "https://api.zotero.org"
LIBRARY_ID = "2533"
API_KEY = environ["ZOTERO_API_KEY"]
HEADERS = {
    "Zotero-API-Version": "3",
    "Zotero-API-Key": API_KEY,
}
WEB_CACHE_DURATION = 67  # minutes
CACHE_DIR_PATH = Path(user_cache_dir("pleiades_reporter"))


class ZoteroAPITooManyRequests(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ZoteroReporter(Reporter):
    """
    Capabilities:
    - Get new bibliographic items since a previous version and produce a list of corresponding PleiadesReport objects, one
      per new item.
    """

    def __init__(self, name: str, user_agent: str, from_header: str):
        headers = HEADERS
        headers["User-Agent"] = user_agent
        headers["From"] = from_header
        Reporter.__init__(
            self,
            name=name,
            api_base_uri=API_BASE,
            headers=headers,
            respect_robots_txt=False,
            expire_after=timedelta(minutes=WEB_CACHE_DURATION),
            cache_control=False,
            cache_dir_path=CACHE_DIR_PATH,
        )
        # self._cache_read()  # sets _last_zot_version and _last_check
        self.logger = getLogger("zotero.ZoteroReporter")

    def check(
        self, override_last_version: str = "", override_last_check: datetime = None
    ) -> list:
        """
        Check for new Zotero records since last check and return a list of reports
        """
        now = datetime.now(tz=pytz.utc)
        if self._wait_until > now:
            return list()
        if self._wait_every_time:
            if self._last_web_request + timedelta(seconds=self._wait_every_time) > now:
                return list()
        if override_last_version:
            old_version = override_last_version
        else:
            old_version = self.last_zot_version
        try:
            new_version = self._check_for_latest_version(
                reference_zot_version=old_version
            )
        except ZoteroAPITooManyRequests as err:
            self.logger.error(str(err))
            return list()
        if new_version is not None and new_version != old_version:
            if override_last_check:
                old_datetime = override_last_check
            else:
                old_datetime = self.last_check
            try:
                new_records = self._zot_get_new_records(
                    since_version=old_version,
                    since_datetime=old_datetime,
                    bypass_cache=True,
                )
            except ZoteroAPITooManyRequests as err:
                self.logger.error(str(err))
                return list()
            now = datetime.now(tz=pytz.utc)
            self.last_zot_version = new_version
            self.last_check = now
        else:
            new_records = list()
        self.logger.debug(f"Got {len(new_records)}")
        return [self._make_report(rec) for rec in new_records]

    def _check_for_latest_version(
        self, bypass_cache=True, reference_zot_version: str = ""
    ) -> str:
        """Ask Zotero API for the latest version of our library"""
        uri = "/".join([API_BASE, "groups", LIBRARY_ID, "items"])
        if reference_zot_version:
            headers = {"If-Modified-Since-Version": reference_zot_version}
        else:
            headers = dict()
        r = self._zot_head(
            uri=uri, additional_headers=headers, bypass_cache=bypass_cache
        )
        self._parse_zot_response_for_backoff(r)
        if r.status_code == 304:
            # no change
            return reference_zot_version
        try:
            return r.headers["Last-Modified-Version"]
        except KeyError as err:
            err.add_note = pformat(r, indent=4)
            raise err

    def _handle_zot_response_codes(self, r: Response):
        bad_code_names = {
            400: "Bad Request",
            403: "Forbidden (Zotero authentication error, e.g., invalid API key or insufficient privileges)",
            404: "Not Found",
            405: "Method Not Allowed",
            417: "Expectation Failed (request included an Expect header, which is unsupported)",
            500: "Internal Server Error (try again later)",
            503: "Service Unavailable (try again later)",
        }
        code = r.status_code
        if code == 200:
            self.logger.debug(f"200 OK")
        elif code == 304:
            self.logger.debug(f"304 Not Modified")
        else:
            addendum = (
                f" when requesting {r.uri}. Headers: {pformat(r.headers, indent=4)}"
            )
            try:
                msg = bad_code_names[code]
            except KeyError:
                raise RuntimeError(
                    f"Unhandled Zotero HTTP status code {code}" + addendum
                )
            raise RuntimeError(msg + addendum)

    def _make_report(self, zot_rec: dict) -> PleiadesReport:
        """
        Create a Pleiades report about a zotero record
        """
        self.logger.debug(pformat(zot_rec, indent=4))

        zot_key = zot_rec["data"]["key"]

        # get citation
        response = self._zot_get(
            uri="https://api.zotero.org/groups/2533/items",
            bypass_cache=False,
            params={
                "itemKey": zot_key,
                "format": "bib",
                "style": "chicago-fullnote-bibliography",
            },
        )
        if response.status_code == 200:
            s = response.text.replace('<?xml version="1.0"?>\n', "")
            s = s + (
                f"  \nBibliographic record in Zotero: https://www.zotero.org/groups/2533/pleiades/items/{zot_key}."
            )
            md = markdownify(s, strip=["div"])
            self.logger.debug(f"md: '{md}'")
        else:
            md = ""

        try:
            st = zot_rec["data"]["shortTitle"]
        except KeyError:
            raise RuntimeError(pformat(zot_rec, indent=4))

        report = PleiadesReport(
            title=f"New in the Pleiades Zotero Library: {st}",
            summary=zot_rec["data"]["title"],
            markdown=md,
            when=zot_rec["data"]["dateAdded"],
        )
        return report

    def _parse_zot_response_for_backoff(self, r: Response):
        """
        Parse the various ways Zotero can tell us to slow down and adjust own config to comply
        """

        # backoff
        # If the API servers are overloaded, the API may include a Backoff: <seconds> HTTP header in responses, indicating that the client should perform the minimum number of requests necessary to maintain data consistency and then refrain from making further requests for the number of seconds indicated.
        try:
            backoff = r.headers["backoff"]
        except KeyError:
            pass
        else:
            self._wait_until = datetime.now(tz=pytz.utc) + timedelta(seconds=backoff)

        # 429 + retry after
        # If a client has made too many requests within a given time period or is making too many concurrent requests, the API may return 429 Too Many Requests with a Retry-After: <seconds> header. Clients receiving a 429 should wait at least the number of seconds indicated in the header before making further requests. They should also reduce their overall request rate and/or concurrency to avoid repeatedly getting 429s, which may result in stricter throttling or temporary blocks.
        if r.status_code == 429:
            try:
                retry_after = r.headers["retry-after"]
            except KeyError:
                self._wait_every_time += 1
            else:
                self._wait_every_time = retry_after
            self._wait_until = datetime.now(tz=pytz.utc) + timedelta(
                seconds=self._wait_every_time
            )
            raise ZoteroAPITooManyRequests(
                f"Retry-After: {self._wait_every_time} (uri: {r.url})"
            )

    def _cache_read(self):
        """
        Read critical Zotero info from the local cache
        - last version checked
        - last datetime checked
        """
        try:
            cached_data = Reporter._cache_read(self)
        except FileNotFoundError:
            # write a version and date that will ensure updates must be checked
            self._last_zot_version = "38632"
            self._last_check = datetime.fromisoformat("2024-01-01T12:12:12+00:00")
            self._cache_write()
        else:
            self._last_zot_version = cached_data["last_version_checked"]
            self._last_check = datetime.fromisoformat(cached_data["last_time_checked"])

    def _cache_write(self):
        """
        Write critical Zotero info to the local cache
        - last version checked
        - last datetime checked
        """
        d = {
            "last_version_checked": self._last_zot_version,
            "last_time_checked": self._last_check.isoformat(),
        }
        Reporter._cache_write(self, d)

    def _zot_head(self, uri, additional_headers, bypass_cache) -> Response:
        """
        Issue an HTTP HEAD request to the Zotero API
        """
        r = self._webi.head(
            uri, additional_headers=additional_headers, bypass_cache=bypass_cache
        )
        self._last_web_request = datetime.now(tz=pytz.utc)
        self.logger.debug(
            f"_zot_head: response headers ({pformat(r.headers, indent=4)}"
        )
        self._parse_zot_response_for_backoff(r)
        return r

    def _zot_get(
        self,
        uri,
        additional_headers: dict = dict(),
        bypass_cache: bool = True,
        params: dict = dict(),
    ) -> Response:
        """
        Issue an HTTP GET request to the Zotero API
        """
        r = self._webi.get(
            uri,
            additional_headers=additional_headers,
            bypass_cache=bypass_cache,
            params=params,
        )
        self._last_web_request = datetime.now(tz=pytz.utc)
        self.logger.debug(f"_zot_get: response headers ({pformat(r.headers, indent=4)}")
        self._parse_zot_response_for_backoff(r)
        return r

    def _zot_get_modified_records(
        self, since_version: str, bypass_cache: bool = True
    ) -> list:
        """
        Get a list of records for top-level items modified since since_version
        """
        uri = "/".join([API_BASE, "groups", LIBRARY_ID, "items", "top"])
        params = {"since": since_version, "format": "json", "includeTrashed": "0"}
        # r = self._webi.get(uri, bypass_cache=bypass_cache, params=params)
        r = self._zot_get(uri=uri, bypass_cache=bypass_cache, params=params)
        if r.status_code == 200:
            modified = r.json()
            return modified
        else:
            self._handle_zot_response_codes(r)
            return list()

    def _zot_get_new_records(
        self, since_version: str, since_datetime: datetime, bypass_cache: bool = True
    ) -> list:
        """
        Get a list of records for top-level items that have been newly added since version and datetime
        """
        candidates = self._zot_get_modified_records(
            since_version=since_version, bypass_cache=bypass_cache
        )
        new = [
            d
            for d in candidates
            if datetime.fromisoformat(d["data"]["dateAdded"]) > since_datetime
        ]
        self.logger.debug(f"_zot_get_new_records: {len(new)}")
        return new

    @property
    def last_zot_version(self) -> str:
        return self._last_zot_version

    @last_zot_version.setter
    def last_zot_version(self, val: str):
        self._last_zot_version = val
        try:
            self._local_cache_writer()
        except AttributeError:
            pass
