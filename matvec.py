#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""matvec.py

Tuesday, September 24 2013
"""

import numpy as np

def mxv(m, v):
    """Multiply matrix and vector.

    m -- 4x4 matrix
    v -- [x, y, z]

    Return the transformed [x, y, z].
    """
    print 'v', type(v)
    vv = v + [1.0]
    print 'vv', vv
    out = np.zeros(4)
    for r in (0, 1, 2, 3):
        result = 0.0
        for c in (0, 1, 2, 3):
            result += vv[c] * m[c, r]
        out[r] = result
    return out[:3]
    
