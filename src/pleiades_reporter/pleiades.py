#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Subclass AtomReporter to deal with Pleiades AtomFeeds
"""
from datetime import datetime, timedelta
from logging import getLogger
from pathlib import Path
from platformdirs import user_cache_dir
from pleiades_reporter.atom import AtomReporter
from pleiades_reporter.report import PleiadesReport
from pleiades_reporter.rss import RSSReporter
from pleiades_reporter.reporter import Reporter
from pleiades_reporter.text import norm, comma_separated_list
from pprint import pformat
import pytz
import re

CACHE_DIR_PATH = Path(user_cache_dir("pleiades_reporter"))

HEADERS = dict()
WEB_CACHE_DURATION = 157  # minutes


class PleiadesRSSReporter(Reporter, RSSReporter):
    def __init__(self, name: str, api_base_uri: str, user_agent: str, from_header: str):
        headers = HEADERS
        headers["User-Agent"] = user_agent
        headers["From"] = from_header
        Reporter.__init__(
            self,
            name=name,
            api_base_uri=api_base_uri,
            headers=headers,
            respect_robots_txt=False,
            expire_after=timedelta(minutes=WEB_CACHE_DURATION),
            cache_control=False,
            cache_dir_path=CACHE_DIR_PATH,
        )
        RSSReporter.__init__(self)
        self.logger = getLogger(f"pleiades.PleiadesRSSReporter({name})")

    def check(self):
        """
        Check for new Pleiades records since last check and return a list of reports
        """
        # get new feed entries that have update dates since our last check
        new_places = list()
        updated_places = list()
        new_records = self._get_latest_entries()
        self.logger.debug(
            f"Got {len(new_records)} feed records {self.last_check.isoformat()}"
        )
        this_check = datetime.now(tz=pytz.utc)
        if new_records:
            pleiades_json = [self._get_pleiades_json(r.link) for r in new_records]
            self.logger.debug(
                f"Got {len(pleiades_json)} json files from Pleiades {this_check.isoformat()}"
            )
            new_places, updated_places = self._determine_changed(pleiades_json)
        self.last_check = this_check
        reports = [self._make_report(place, "new") for place in new_places]
        reports.extend(
            [self._make_report(place, "updated") for place in updated_places]
        )
        return reports

    def _cache_read(self):
        """
        Read critical Pleiades info from the local cache
        - last datetime checked
        """
        try:
            cached_data = Reporter._cache_read(self)
        except FileNotFoundError:
            # write a date that will ensure updates must be checked
            self._last_check = datetime.fromisoformat("2024-01-01T12:12:12+00:00")
            self._cache_write()
        else:
            self._last_check = datetime.fromisoformat(cached_data["last_time_checked"])

    def _cache_write(self):
        """
        Write critical Pleiades info to the local cache
        - last datetime checked
        """
        d = {
            "last_time_checked": self._last_check.isoformat(),
        }
        Reporter._cache_write(self, d)

    def _determine_changed(self, pleiades_json: list) -> tuple:

        # determine newly published places
        pleiades_first_pub_dates = list()
        pleiades_latest_modification_dates = list()
        for j in pleiades_json:
            first_pub_date, latest_mod_date = self._get_event_dates(j)
            pleiades_first_pub_dates.append(first_pub_date)
            pleiades_latest_modification_dates.append(latest_mod_date)

        new_places = list()
        updated_places = list()
        for i, pj in enumerate(pleiades_json):
            published_dt = pleiades_first_pub_dates[i]
            modified_dt = pleiades_latest_modification_dates[i]
            self.logger.debug(
                f"DETERMINATION: pid:{pj['id']} published:{published_dt.isoformat()} modified:{modified_dt.isoformat()}"
            )
            if pleiades_first_pub_dates[i] >= self.last_check:
                new_places.append(pj)
            elif pleiades_latest_modification_dates[i] >= self.last_check:
                updated_places.append(pj)
        self.logger.debug(f"New places: {len(new_places)}")
        self.logger.debug(f"Updated places: {len(updated_places)}")
        return (new_places, updated_places)

    def _get_event_dates(self, pleiades_json: dict) -> tuple:
        publication_events = list()
        modification_events = list()
        for event in pleiades_json["history"]:
            modification_events.append(event)
            try:
                action = event["action"]
            except KeyError:
                pass  # irrelevant changes
            else:
                if action == "Publish externally":
                    publication_events.append(event)
        publication_events = sorted(
            publication_events, key=lambda e: e["modified"], reverse=True
        )
        modification_events = sorted(
            modification_events, key=lambda e: e["modified"], reverse=True
        )
        latest_mod_date = datetime.fromisoformat(modification_events[0]["modified"])
        first_pub_date = datetime.fromisoformat(publication_events[-1]["modified"])
        return (first_pub_date, latest_mod_date)

    def _get_pleiades_json(self, puri: str):
        juri = puri + "/json"
        r = self._webi.get(uri=juri)
        if r.status_code == 200:
            return r.json()
        r.raise_for_status

    def _make_report(self, place_json: dict, nature: str = "new") -> PleiadesReport:
        """
        Create a Pleiades report about a new Pleiades place resource
        """
        self.logger.debug(pformat(place_json, indent=4))
        creators = comma_separated_list([c["name"] for c in place_json["creators"]])
        contributors = comma_separated_list(
            [c["name"] for c in place_json["contributors"]]
        )

        title_names = [
            norm(n) for n in re.split(r"[/,]", place_json["title"]) if "(" not in n
        ]
        title_names = {n.replace("?", "") for n in title_names}
        names = set()
        for nrec in place_json["names"]:
            names.update({norm(n) for n in nrec["romanized"].split(",")})
            attested = norm(nrec["attested"])
            if attested:
                names.add(attested)
        names.update(title_names)
        names = sorted(list(names))

        md = (
            place_json["description"]
            + (".", "")[place_json["description"][-1] == "."]
            + "  \n\n"
            + f"Resource created by {creators}"
            + (".", f" with contributions by {contributors}.")[len(contributors) > 0]
            + "  \n\n"
            + f"Canonical URI: https://pleiades.stoa.org/places/{place_json['id']}"
            + "  \n\nNames: "
            + ", ".join(names)
        )

        # determine when
        first_pub_date, latest_mod_date = self._get_event_dates(place_json)
        if nature == "new":
            when = first_pub_date
        else:
            when = latest_mod_date

        report = PleiadesReport(
            title=f"{nature.title()} place resource in the Pleiades gazetteer: {place_json['title']}",
            summary=place_json["description"],
            markdown=md,
            when=when.strftime("%Y-%m-%d"),
        )
        return report


class PleiadesBlogReporter(Reporter, AtomReporter):
    def __init__(self, name: str, api_base_uri: str, user_agent: str, from_header: str):
        self._tag_rules = [
            (
                re.compile(
                    r"^blogged: (last week|last (\d+ |two |three )weeks) in .+$"
                ),
                [
                    "ancientGeography",
                    "ancientHistory",
                    "archaeology",
                    "digitalHumanities",
                    "gazetteers",
                    "HGIS",
                    "LinkedOpenData",
                    "PleiadesGazetteer",
                ],
            )
        ]
        self._body_paras = [
            (
                re.compile(
                    r"^blogged: (last week|last (\d+ |two |three )weeks) in .+$"
                ),
                [
                    (
                        "A linked list of all affected gazetteer entries, as well "
                        "as summaries of changes and an overview map, are available "
                        "in the blog post."
                    )
                ],
            )
        ]
        headers = HEADERS
        headers["User-Agent"] = user_agent
        headers["From"] = from_header
        Reporter.__init__(
            self,
            name=name,
            api_base_uri=api_base_uri,
            headers=headers,
            respect_robots_txt=False,
            expire_after=timedelta(minutes=WEB_CACHE_DURATION),
            cache_control=False,
            cache_dir_path=CACHE_DIR_PATH,
        )
        RSSReporter.__init__(self)
        self.logger = getLogger(f"pleiades.PleiadesBlogReporter({name})")

    def check(self):
        """
        Check for new Pleiades blog posts since last check and return a list of reports
        """
        # get new feed entries that have update dates since our last check
        new_entries = self._get_new_entries(since=self.last_check)
        self.logger.debug(
            f"Got {len(new_entries)} blog feed entries updated since {self.last_check.isoformat()}"
        )
        this_check = datetime.now(tz=pytz.utc)
        self.last_check = this_check
        return [self._make_report(e) for e in new_entries]

    def _add_body_to_report(self, report: PleiadesReport) -> PleiadesReport:
        for rx, paras in self._body_paras:
            m = rx.match(report.title.lower())
            if m is not None:
                all_paras = [report.markdown]
                all_paras.extend(paras)
                report.markdown = "   \n\n".join(all_paras)
                break
        return report

    def _add_tags_to_report(self, report: PleiadesReport) -> PleiadesReport:
        for rx, tags in self._tag_rules:
            m = rx.match(report.title.lower())
            if m is not None:
                report.tags = tags
                break
        return report

    def _cache_read(self):
        """
        Read critical Pleiades info from the local cache
        - last datetime checked
        """
        try:
            cached_data = Reporter._cache_read(self)
        except FileNotFoundError:
            # write a date that will ensure updates must be checked
            self._last_check = datetime.fromisoformat("2024-01-01T12:12:12+00:00")
            self._cache_write()
        else:
            self._last_check = datetime.fromisoformat(cached_data["last_time_checked"])

    def _cache_write(self):
        """
        Write critical Pleiades info to the local cache
        - last datetime checked
        """
        d = {
            "last_time_checked": self._last_check.isoformat(),
        }
        Reporter._cache_write(self, d)

    def _make_report(self, feed_entry: dict) -> PleiadesReport:
        """
        Create a Pleiades report about a new Pleiades blog post
        """
        self.logger.debug(pformat(feed_entry, indent=4))
        md = "   \n\n".join((feed_entry.summary, feed_entry.link))
        report = PleiadesReport(
            title=f"Blogged: {feed_entry.title}",
            summary=feed_entry.summary,
            markdown=md,
            when=feed_entry.updated,
        )
        report = self._add_body_to_report(report)
        report = self._add_tags_to_report(report)
        return report