#
# This file is part of pleiades_reporter
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manipulate text strings
"""

import textnorm


def norm(s: str, preserve: list = list(), trim: bool = True) -> str:
    """Normalize unicode and whitespace in a string."""
    return textnorm.normalize_space(
        textnorm.normalize_unicode(s), preserve=preserve, trim=trim
    )
