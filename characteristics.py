#!/usr/bin/env python
################################################################################
# Gather characteristics work in one place

import argparse
import math

from libnoisEE import *

def filter_characteristics(white, state):
    rev_state = 1 - state
    knee_frac = (0.00022856304700783622
                 + 0.41420297628235303 * rev_state
                 - 0.42118671936182317 * rev_state**2
                 + 0.42118671936182317 * rev_state**3
                 + 0.892743444761949 * rev_state**4)
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
