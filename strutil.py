#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""strutil.py

Monday, September  9 2013
"""

import re

FMTIN = '%.4f"'                 # linear dimension inch format string
FMTMM = '%.3fmm'                # linear dimension millimeter format string
FMTAN = u'%.2f°'                # angle dimension format string
FMTRIN = 'R%.4f"'               # radius dimension inch format string
FMTRMM = 'R%.3fmm'              # radius dimension millimeter format string

def ffmt(fmt, value):
    """Format the dimension value.

    fmt -- format string, "%.3f" for example
    value -- number

    Whole numbers with a float format have all but one trailing zero removed.
    1 => 1.0

    Non-numeric suffixes are handled. If fmt is '%.3fmm' and value is 3.14,
    the resulting string will be '3.14mm'. A value of 3 will result in
    '3.0mm' (not 3.000mm).

    Return the formatted string.
    """
    s = fmt % value
    # find any non-numeric suffix
    mo = re.match(ur'^.+?([^\d]+)$', s)
    if mo:
        s = s[:mo.start(1)].rstrip('0')
        if s[-1] == '.':
            s += '0'
        s += mo.group(1)
    else:
        s = s.rstrip('0')
        if s[-1] == '.':
            s += '0'
    return s

if __name__ == '__main__':
    print ffmt("%.3fmm", 3.14)
    print ffmt("%.3fmm", 3)
    print ffmt("%.3fmm", 3.)
    print ffmt("%.3fmm", 3.14159)
    print ffmt('%.4f"', 3.14)
    print ffmt('%.4f"', 3)
    print ffmt('%.4f"', 3.)
    print ffmt('%.4f"', 3.14159)
    print ffmt("R%.3fmm", 3.14)
    print ffmt("R%.3fmm", 3)
    print ffmt("R%.3fmm", 3.)
    print ffmt("R%.3fmm", 3.14159)
    print ffmt('R%.3f"', 3.14)
    print ffmt('R%.3f"', 3)
    print ffmt('R%.3f"', 3.)
    print ffmt('R%.3f"', 3.14159)
    print ffmt(u'%.2f°', 3.14)
    print ffmt(u'%.2f°', 3)
    print ffmt(u'%.2f°', 3.)
    print ffmt(u'%.2f°', 3.14159)

