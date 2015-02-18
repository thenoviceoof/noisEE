#!/usr/bin/env python
################################################################################
# Mess around with different ways to move filters around

import argparse
import math
import numpy

from characteristics import filter_characteristics
from libnoisEE import *

def ideal_filter(white, state, steps=1024, high_freq=SAMPLE_RATE/2):
    print white, state
    knee_freq, pass_band = filter_characteristics(white, state)
    print knee_freq, pass_band
    stops = [float(high_freq) * (99.1/100)**i for i in range(steps)]
    feed = [1/(s/knee_freq + 1) for s in stops]
    feedb = [pass_band + 20 * math.log(f, 10) for f in feed]
    return stops, feedb

def main(params):
    filters = [(float(params[2*i]), float(params[2*i+1]))
               for i in range(len(params)/2)]
    levels = []
    for fil in filters:
        white, state = fil
        xs, ys = ideal_filter(white, state)
        plt.plot(xs, ys)
        levels.append(ys)

    # Add up the decibels
    levels = numpy.transpose(levels)
    total = [10 * math.log(sum([10**(y/10.) for y in ys]), 10) for ys in levels]

    plt.plot(xs, total, label='total')
    plt.xscale('log')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('params', nargs='+')

    args = parser.parse_args()

    assert len(args.params) % 2 == 0, 'Need even number of parameters'
    main(args.params)
