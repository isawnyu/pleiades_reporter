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
import logging
from pleiades_reporter.zotero import ZoteroReporter
from time import sleep

logger = logging.getLogger(__name__)

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%I"
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


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
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
                for i, report in enumerate(
                    sorted(
                        reports[report_count : len(reports)],
                        key=lambda r: r.when,
                        reverse=True,
                    )
                ):
                    print(
                        f"{i+1}. {report.title} ({report.when.strftime(DEFAULT_DATETIME_FORMAT)})"
                    )
                # make decisions about what to publish here
                # TBD
                report_count = len(reports)
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
