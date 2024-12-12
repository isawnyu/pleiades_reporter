#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Python 3 script template (changeme)
"""

from airtight.cli import configure_commandline
from datetime import datetime, timedelta
from itertools import chain
import logging
from mastodon import Mastodon
from os import environ
from pathlib import Path
from pleiades_reporter.go_to_social import GoToSocialChannel
from pleiades_reporter.zotero import ZoteroReporter
from pleiades_reporter.text import norm
from pprint import pformat
from time import sleep

bot_api = None
logger = logging.getLogger(__name__)

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DEFAULT_LOG_LEVEL = logging.WARNING
OPTIONAL_ARGUMENTS = [
    [
        "-l",
        "--loglevel",
        "NOTSET",
        "desired logging level ("
        + "case-insensitive string: DEBUG, INFO, WARNING, or ERROR",
        False,
    ],
    ["-v", "--verbose", False, "verbose output (logging level == INFO)", False],
    [
        "-w",
        "--veryverbose",
        False,
        "very verbose output (logging level == DEBUG)",
        False,
    ],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]


def rangeString(commaString):
    """
    Code by ninjagecko on stackoverflow:
    https://stackoverflow.com/questions/6405208/how-to-convert-numeric-string-ranges-to-a-list-in-python#answer-6405816
    """

    def hyphenRange(hyphenString):
        x = [int(x) for x in hyphenString.split("-")]
        return range(x[0], x[-1] + 1)

    return chain(*[hyphenRange(r) for r in commaString.split(",")])


def get_user_disposition(new_reports: list) -> bool:
    """
    Solicit and process user input at the command line.
    """
    cmd = norm(input("cmd>>> "))
    if not cmd:
        return
    cmd_lower = cmd.lower()
    if cmd_lower in ["q", "quit", "exit"]:
        exit()
    if cmd_lower.startswith("preview "):
        return preview_reports(" ".join(cmd_lower.split()[1:]), new_reports)
    if cmd_lower.startswith("publish ") or cmd_lower.startswith("post "):
        return publish_reports(" ".join(cmd_lower.split()[1:]), new_reports)


def preview_reports(predicate: str, new_reports: list) -> bool:
    """
    Preview reports selected by user.
    """
    items = rangeString(predicate)
    for i in [int(n) - 1 for n in list(items)]:
        print("-" * 72)
        print("\n\n".join([new_reports[i].title, str(new_reports[i])]))
    print("-" * 72)
    return True


def publish_reports(predicate: str, new_reports: list) -> bool:
    """
    Send reports to social media
    """
    global bot_api

    items = rangeString(predicate)
    for i in [int(n) - 1 for n in list(items)]:
        status = bot_api.status_post(
            status="\n\n".join([new_reports[i].title, str(new_reports[i])]),
            language="en",
        )
        logger.debug(pformat(status, indent=4))
    return False


def main(**kwargs):
    """
    main function
    """
    global bot_api

    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    access_token = environ["BOTSINBOX_ACCESS_TOKEN"]
    bot_api = Mastodon(
        access_token=access_token,
        api_base_url="https://botsinbox.net",
        version_check_mode="none",
    )
    reporters = {"zotero": ZoteroReporter()}
    periods = {"zotero": 180}
    dawn_of_time = datetime(year=1970, month=1, day=1)
    last_execution = {"zotero": dawn_of_time}
    reports = list()
    report_count = 0
    LOOP_PERIOD = 180
    while True:
        try:
            for r_key, reporter in reporters.items():

                if datetime.now() - last_execution[r_key] > timedelta(
                    seconds=periods[r_key]
                ):
                    logger.info(f"Checking reporter '{r_key}'")
                    reports.extend(reporter.check())
            if len(reports) > report_count:
                print(f"{len(reports) - report_count} new reports have been generated:")
                new_reports = sorted(
                    reports[report_count : len(reports)],
                    key=lambda r: r.when,
                    reverse=True,
                )
                for i, report in enumerate(new_reports):
                    print(
                        f"{i+1}. {report.title} ({report.when.strftime(DEFAULT_DATETIME_FORMAT)})"
                    )
                report_count = len(reports)
                another_cmd = True
                while another_cmd:
                    another_cmd = get_user_disposition(new_reports)
            print(
                f"Sleeping for {LOOP_PERIOD} seconds (i.e., until {(datetime.now() + timedelta(seconds=LOOP_PERIOD)).strftime(DEFAULT_DATETIME_FORMAT)})"
            )
            sleep(LOOP_PERIOD)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
