#!/usr/bin/env python
################################################################################
# Gather characteristics work in one place

import argparse
import math

from libnoisEE import *

def filter_characteristics(white, state):
    knee_invt = 1/(-0.30146697706424969 +
                   3.7248300949823099 * state +
                   -5.5472369176016798 * state**2 +
                   4.5164881456764085 * state**3 +
                   -1.3932002981788807 * state**4)
    if knee_invt < 0:
        knee_invt = 10000000
    knee_frac = math.log(knee_invt, 10)

    knee_freq = (SAMPLE_RATE/2) * knee_frac
    pass_band = (6.02059991328 * math.log(white, 2)
                 + 14.036948327785755 * state
                 - 22.850386042107317 * state**2
                 + 34.797524550144153 * state**3)

    assert knee_freq >= 0, knee_freq

    return (knee_freq,pass_band)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--white', type=float, default=1.0)
    parser.add_argument('-s', '--state', type=float, default=0.0)

    args = parser.parse_args()

    knee_freq, pass_band = filter_characteristics(args.white, args.state)
    print (knee_freq, pass_band)
