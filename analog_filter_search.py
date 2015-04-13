#!/usr/bin/env python
################################################################################
# Calculate the passband functions given knees

import argparse
import math
import numpy

from characteristics import filter_characteristics
from libnoisEE import *

def ideal_filter(knee_freq, pass_band, steps=1024, high_freq=SAMPLE_RATE/2):
    stops = [float(high_freq) * (99.1/100)**i for i in range(steps)]
    feed = [1/((s/knee_freq)**2 + 1)**0.5 for s in stops]
    feedb = [pass_band + 20 * math.log(f, 10) for f in feed]
    return stops, feedb

def fit_filter_combine(params):
    levels = []
    for knee,band in params:
        levels.append(ideal_filter(knee, band)[1])

    # Add up the decibels
    levels = numpy.transpose(levels)
    total = [10 * math.log(sum([10**(y/10.) for y in ys]), 10) for ys in levels]

    # Generate the log frequency (y) for the spectra data (x),
    # for a true lg-lg plot, removing the constant (to avoid -inf)
    freq = ideal_filter(knee, band)[0]
    lg_freq = numpy.log10(freq)

    # fit a line to the dbs
    fit, error, _, _, rcond = numpy.polyfit(lg_freq, total, 1, full=True)
    err = error[0]**0.5
    m, b = fit

    # if it doesn't keep the final knee at 0, toss it
    if abs(m * lg_freq[0] + b) > 1:
        err = 100
    return err

def main(knees, slope_step=-0.1, slope_start=0.0, slope_end=-6.0):
    # make sure knees are smallest->largest
    knees = sorted(knees)
    # make sure there's a "white noise" source
    if knees[-1] < SAMPLE_RATE/2:
        knees.append(4 * SAMPLE_RATE)

    # init the filters to super soft, except for white
    params = [[knee, -100] for knee in knees]
    params[-1][1] = 0
    # make sure the slope steps and start/end agree
    assert slope_end < slope_start
    assert slope_step < 0
    # For each slope...
    slope_steps = int((slope_end - slope_start)/slope_step)
    for slope in [0.0]:
    #for slope in [slope_step * i for i in range(slope_steps)]: !!!
        best_params = params
        best_fit = fit_filter_combine(params)
        # Tweak the passbands
        while best_fit > 0.5:
            for j in range(20):
                jit_params = [[knee, band + 0.5 * random.random()]
                              for knee,band in best_params]
                # filter/combine
                fit = fit_filter_combine(jit_params)
                # Fit each, use the best fit
                if fit > best_fit:
                    best_fit = fit
                    best_params = jit_params
        params = best_params
        print params
        print best_fit

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('knees', nargs='+', type=float)

    args = parser.parse_args()

    main(args.knees)
