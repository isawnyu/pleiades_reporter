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
from pathlib import Path
from validators import url as valid_uri
from urllib.parse import urlparse
from webiquette.webi import Webi


class Reporter:
    def __init__(
        self,
        api_base_uri: str,
        headers: dict,
        respect_robots_txt: bool,
        expire_after: timedelta,
        cache_control: bool,
        cache_dir_path: Path,
    ):
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
        self._wait_every_time = 0  # seconds to wait before each check
