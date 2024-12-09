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
from datetime import datetime, timedelta
from logging import getLogger
from os import environ
from pathlib import Path
from platformdirs import user_cache_dir
from pprint import pprint, pformat
from requests import Response
from urllib.parse import urlparse
from webiquette.webi import Webi

API_BASE = "https://api.zotero.org"
LIBRARY_ID = "2533"
API_KEY = environ["ZOTERO_API_KEY"]
HEADERS = {
    "User-Agent": "PleiadesReporter/0.1 (+https://pleiades.stoa.org)",
    "Zotero-API-Version": "3",
    "Zotero-API-Key": API_KEY,
}
WEB_CACHE_DURATION = 67  # minutes


class ZoteroReporter:
    """
    Capabilities:
    - Get new bibliographic items since a previous version and produce a list of corresponding PleiadesReport objects, one
      per new item.
    """

    def __init__(
        self,
    ):
        self._webi = Webi(
            netloc=urlparse(API_BASE).netloc,
            headers=HEADERS,
            respect_robots_txt=False,
            expire_after=timedelta(minutes=WEB_CACHE_DURATION),
            cache_control=False,
            cache_dir=str(Path(user_cache_dir("pleiades_reporter"))),
        )
        # TBD: get last version number and datetime checked and known keys from cache
        self._last_zot_version = "38632"
        self._last_check = datetime(year=1900, month=1, day=1)
        self._known_zot_keys = set()
        self.logger = getLogger("zotero.ZoteroReporter")

    @property
    def last_zot_version(self):
        return self._last_zot_version

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
        return r.headers["Last-Modified-Version"]

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

    def _parse_zot_response_for_backoff(self, r: Response):
        """
        Parse the various ways Zotero can tell us to slow down and adjust own config to comply
        """
        try:
            backoff = r.headers["backoff"]
        except KeyError:
            pass
        else:
            # TBD wait backoff seconds
            raise NotImplementedError(f"Got response header backoff: {backoff}")
        if r.status_code == 429:
            # TBD: Get value of Retry-After: <seconds> header and wait at least the number of seconds indicated in the header before making further requests.
            raise NotImplementedError(f"Got status code 429 from Zotero API")

    def _zot_head(self, uri, additional_headers, bypass_cache) -> Response:
        """
        Issue an HTTP HEAD request to the Zotero API
        """
        r = self._webi.head(
            uri, additional_headers=additional_headers, bypass_cache=bypass_cache
        )
        self.logger.debug(
            f"_zot_head: response headers ({pformat(r.headers, indent=4)}"
        )
        self._parse_zot_response_for_backoff(r)
        return r

    def _zot_get(self, uri, additional_headers, bypass_cache) -> Response:
        """
        Issue an HTTP GET request to the Zotero API
        """
        r = self._webi.get(
            uri, additional_headers=additional_headers, bypass_cache=bypass_cache
        )
        self.logger.debug(f"_zot_get: response headers ({pformat(r.headers, indent=4)}")
        self._parse_zot_response_for_backoff(r)
        return r

    def _zot_get_modified_records(self, since_version: str, bypass_cache: bool) -> list:
        """
        Get a list of records for top-level items modified since since_version
        """
        uri = "/".join([API_BASE, "groups", LIBRARY_ID, "items", "top"])
        params = {"since": since_version, "format": "json", "includeTrashed": "0"}
        r = self._webi.get(uri, bypass_cache=bypass_cache, params=params)
        if r.status_code == 200:
            modified = r.json()
            self.logger.debug(f"_zot_get_modified_records: {len(modified)}")
            return modified
        else:
            self._handle_zot_response_codes(r)
            return list()

    def _zot_get_new_records(
        self, since_version: str, since_datetime: datetime, bypass_cache: bool
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
