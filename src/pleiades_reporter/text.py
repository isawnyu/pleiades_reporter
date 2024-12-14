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


def comma_separated_list(s: str | list):
    if isinstance(s, str):
        words = norm(s).split()
    elif isinstance(s, list):
        words = [norm(w) for w in s]
        words = [w for w in words if w]
    else:
        raise TypeError(type(s))
    if not words:
        return ""
    wcount = len(words)
    if wcount == 1:
        return " ".join(words)
    elif wcount == 2:
        return " and ".join(words)
    else:
        result = ", ".join(words[:-1])
        result = result + " and " + words[-1]
        return result
