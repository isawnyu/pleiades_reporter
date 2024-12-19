#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Subclass AtomReporter to deal with Pleiades AtomFeeds
"""
from copy import deepcopy
from datetime import datetime, timedelta, date
from feedparser.util import FeedParserDict
import json
from logging import getLogger
from pathlib import Path
from platformdirs import user_cache_dir
from pleiades_reporter.atom import AtomReporter
from pleiades_reporter.dates import iso2date
from pleiades_reporter.report import PleiadesReport
from pleiades_reporter.rss import RSSReporter, BetterRSSHandler
from pleiades_reporter.reporter import Reporter
from pleiades_reporter.text import norm, comma_separated_list
from pprint import pformat
import pytz
import re
from urllib.parse import urlparse, urlunparse

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
        RSSReporter.__init__(self, cache_dir_path=CACHE_DIR_PATH)
        self.logger = getLogger(f"pleiades.PleiadesRSSReporter({name})")
        self.rxx_who = [
            re.compile(r" by @(?P<who>[a-zA-Z]+)"),
            re.compile(r"@(?P<who>[a-zA-Z]+)"),
        ]
        with open("data/who.json", "r", encoding="utf-8") as f:
            self._who = json.load(f)
        del f

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
            if pleiades_first_pub_dates[i] >= datetime(
                year=self.last_check.year,
                month=self.last_check.month,
                day=self.last_check.day,
                tzinfo=pytz.utc,
            ):
                new_places.append(pj)
            elif pleiades_latest_modification_dates[i] >= datetime(
                year=self.last_check.year,
                month=self.last_check.month,
                day=self.last_check.day,
                tzinfo=pytz.utc,
            ):
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

    def _get_recent_history(self, obj: dict, cutoff_date: datetime) -> list:
        recent_history = list()
        full_history = sorted(
            obj["history"], key=lambda event: event["modified"], reverse=True
        )
        from_baseline = False
        for e in full_history:
            try:
                comment = e["action"]
            except KeyError:
                comment = e["comment"]
            if comment == "Publish externally":
                break
            elif comment == "Baseline created":
                from_baseline = True
                break
            else:
                recent_history.append(e)
        if not from_baseline:
            # prune too-early direct edits from recent history
            pruned_history = list()
            for e in recent_history:
                if datetime.fromisoformat(e["modified"]) < cutoff_date:
                    break
                else:
                    pruned_history.append(e)
            recent_history = pruned_history
        after_cutoff = [
            e
            for e in recent_history
            if datetime.fromisoformat(e["modified"]) >= cutoff_date
        ]
        if after_cutoff:
            return recent_history
        else:
            return list()

    def _get_modification_summary(self, pj: dict, cutoff_date: datetime) -> str:
        """
        Create a string summarizing all modifications to this place and its children
        """
        recent_history = self._get_recent_history(pj, cutoff_date)
        modifications = set()
        people = set()
        for e in recent_history:
            who = e["modifiedBy"]
            try:
                mod = e["action"]
            except KeyError:
                mod = e["comment"]
            people.add(who)
            # more people in comment
            if "@" in mod:
                for rx in self.rxx_who:
                    hits = rx.findall(mod)
                    if hits:
                        people.update([h for h in hits])
                        mod = rx.sub("", mod)
            mods = [norm(m) for m in mod.split(";")]
            mods = [m for m in mods if m]
            modifications.update(mods)

        # extract and parse relevant history from subordinate objects
        more_mods = dict()
        for k in ["names", "locations", "connections"]:
            for obj in pj[k]:
                recent_history = self._get_recent_history(obj, cutoff_date)
                mods = list()
                for e in recent_history:
                    who = e["modifiedBy"]
                    try:
                        mod = e["action"]
                    except KeyError:
                        mod = e["comment"]
                    people.add(who)
                    # more people in comment
                    if "@" in mod:
                        for rx in self.rxx_who:
                            hits = rx.findall(mod)
                            if hits:
                                people.update([h for h in hits])
                                mod = rx.sub("", mod)
                    mods = [norm(m) for m in mod.split(";")]
                    mods = [m for m in mods if m]
                if mods:
                    more_mods[f"{k}:{obj["id"]}"] = mods

        # look up names for all the people listed and convert to a string
        people = [self._who[p.lower()] for p in people]
        people = [p for p in people if p]
        people = sorted(
            people, key=lambda p: " ".join(p.split()[1:]) + f" {p.split()[0]}"
        )
        people_string = comma_separated_list(list(people))

        # cleanup and normalize the modification strings
        normalized_modifications = list()
        for mod in modifications:
            words = mod.split()
            if len(words) == 1:
                if words[0] in {"description", "summary", "placetype", "title"}:
                    words = ["modified", words[0]]
                else:
                    words = words
            new_words = list()
            for word in words:
                new_word = word
                if new_word.lower() in {"update"}:
                    new_word = f"{new_word}d"  # past tense
                if new_word in {"Updated", "Edited"}:
                    new_word = new_word.lower()
                new_words.append(new_word)
            normalized_modifications.append(" ".join(new_words))
        if len(normalized_modifications) > 1:
            normalized_modifications = [
                m for m in normalized_modifications if m.lower() != "edited"
            ]
        normalized_modifications = sorted(normalized_modifications)
        mod_in_context = {"location": set(), "name": set(), "connection": set()}
        for mod_k, mods in more_mods.items():
            if not mods:
                continue
            for k in mod_in_context.keys():
                if mod_k.startswith(k):
                    mod_in_context[k].update(mods)
        for k, mods in mod_in_context.items():
            if mods:
                normalized_modifications.append(f"{k}s: {', '.join(sorted(mods))}")
        modification_string = "; ".join(normalized_modifications)

        return f"Modifications by {people_string}: {modification_string}"

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
            if nrec["attested"] is not None:
                attested = norm(nrec["attested"])
                if attested:
                    names.add(attested)
        names.update(title_names)
        names = sorted(list(names))

        # determine when
        first_pub_date, latest_mod_date = self._get_event_dates(place_json)
        if nature == "new":
            when = first_pub_date
        else:
            when = latest_mod_date

        # construct the body
        extra = ""
        if nature == "updated":
            extra = self._get_modification_summary(place_json, when)
            if extra:
                extra = f"  \n\n{extra}"
        description = place_json["description"].strip()
        if not description:
            description = "[no description]"
        md = (
            description
            + (".", "")[description[-1] == "."]
            + "  \n\n"
            + f"Resource created by {creators}"
            + (".", f" with contributions by {contributors}.")[len(contributors) > 0]
            + "  \n\n"
            + f"Canonical URI: https://pleiades.stoa.org/places/{place_json['id']}"
            + "  \n\nNames: "
            + ", ".join(names)
            + extra
        )

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
        RSSReporter.__init__(self, cache_dir_path=CACHE_DIR_PATH)
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


class PleiadesChangesReporter(Reporter, BetterRSSHandler):
    def __init__(
        self,
        name: str,
        api_base_uri: str,
        user_agent: str,
        from_header: str,
        cache_dir_path=CACHE_DIR_PATH,
    ):
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
            cache_dir_path=cache_dir_path,
        )
        BetterRSSHandler.__init__(self, cache_path=cache_dir_path)
        self.feed_url = api_base_uri
        self.place_base_uri = "https://pleiades.stoa.org/places/"
        self.logger = getLogger(f"PleiadesChangesReporter::{name}")

    def check(self) -> list:
        """
        Check for new Pleiades records since last check and return a list of reports
        """
        new_dated_entries = self._fetch(
            feed_url=self.feed_url, web_interface=self._webi, filter=True
        )
        if not new_dated_entries:
            return list()

        new_reports = [
            self._make_report(e, dt_iso, self._get_place_json(e.guid))
            for e, dt_iso in new_dated_entries
        ]
        return new_reports

    def _cache_read(self):
        """
        Read critical info from the local cache
        """
        pass

    def _cache_write(self):
        """
        Write critical info to the local cache
        """
        pass

    def _filter_histories(self, histories: dict, dt_iso: str) -> dict:
        """
        Return a dictionary like the one returned by _get_histories, but only with
        object histories that span the date in dt_iso
        """
        recent_histories = dict()
        horizon = iso2date(dt_iso)
        for k, v in histories.items():
            if k == "place":
                h = self._filter_history(v, horizon)
                if h:
                    recent_histories["place"] = h
            else:
                for obj_id, obj_h in v:
                    h = self._filter_history(obj_h, horizon)
                    if h:
                        try:
                            recent_histories[k]
                        except KeyError:
                            recent_histories[k] = list()
                        recent_histories[k].append((obj_id, h))
        return recent_histories

    def _filter_history(self, history: list, horizon: date) -> list:
        """
        Filter a history list down to strings of publication/checkin since horizon, including
        their antecedents
        """
        normed_history = self._normalize_history(history)
        sorted_history = sorted(
            normed_history, key=lambda item: item["date"], reverse=True
        )
        self.logger.debug(f"horizon: {horizon}")
        self.logger.debug(f"normed_history: {pformat(normed_history, indent=4)}")
        self.logger.debug(f"sorted_history: {pformat(sorted_history, indent=4)}")

        horizon_index = len([e for e in sorted_history if e["date"] >= horizon]) - 1
        if horizon_index == -1:
            # nothing happened in the relevant time frame
            return list()
        self.logger.debug(f"horizon_index: {horizon_index}")

        for i, e in enumerate(sorted_history[: horizon_index + 1]):
            if e["status"] == "Publish externally":
                break
        if i >= 0 and i <= horizon_index:
            # this is a newly-published item, possibly with (irrelevant) quick fixes thereafter
            return [sorted_history[i]]

        for i, e in enumerate(sorted_history):
            if e["status"] in {"Publish externally", "Baseline created"}:
                break
        return sorted_history[:i]

    def _make_report(
        self, entry: FeedParserDict, dt_iso: str, pleiades_json: dict
    ) -> PleiadesReport:
        # get histories from relevant place and sub-objects
        histories = self._get_histories(pleiades_json)
        # filter objects to consider only those whose histories include events since the cutoff
        histories = self._filter_histories(histories, dt_iso)
        # parse relevant histories to produce summaries for each object
        # combine object summaries to make an overall summary for the report
        # construct and return the report
        return None

    def _normalize_history(self, history: list) -> list:
        """
        process an event list:
        - assign UTC dates to each event
        - normalize 'comment' and 'action' into 'status'
        """
        normed_history = list()
        for event in history:
            normed_history.append(self._normalize_event(event))
        return normed_history

    def _normalize_event(self, event: dict) -> dict:
        """
        Add a python date and a status string to the event
        """
        e = deepcopy(event)
        e["date"] = iso2date(event["modified"])
        status = ""
        try:
            status = event["comment"]
        except KeyError:
            pass
        try:
            status = event["action"]
        except KeyError:
            pass
        e["status"] = status
        return e

    def _get_histories(self, pleiades_json: dict) -> dict:
        """
        Return a dictionary containing all the histories of all objects in this place object
        """
        histories = {"place": pleiades_json["history"]}
        for k in ["locations", "names", "connections"]:
            histories[k] = list()
            for obj in pleiades_json[k]:
                histories[k].append((obj["id"], obj["history"]))
        return histories

    def _get_place_json(self, obj_url: str) -> dict:
        parts = urlparse(obj_url)
        m = re.match(r"^/places/(\d+).*$", parts.path)
        if m is None:
            raise ValueError(obj_url)
        pid = m.group(1)
        new_path = f"/places/{pid}/json"
        new_parts = (parts.scheme, parts.netloc, new_path, "", "", "")
        new_url = urlunparse(new_parts)
        r = self._webi.get(new_url)
        if r.status_code == 200:
            return r.json()
        else:
            r.raise_for_status()
