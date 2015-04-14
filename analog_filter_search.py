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

    return m, b, err, lg_freq[0]

def combine_errors(m, b, var_err, min_freq, slope):
    org_err = abs(m * min_freq + b)
    slp_err = abs(m - slope)
    err = 5 * var_err + org_err + slp_err
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
    slope = slope_start
    while slope >= slope_end:
        best_params = params
        m, b, var_err, min_freq = fit_filter_combine(params)
        best_err = combine_errors(m, b, var_err, min_freq, slope)
        # Tweak the passbands
        while best_err > 2:
            for j in range(20):
                jit_params = [[knee, band + 0.5 * random.random()]
                              for knee,band in best_params]
                # apply filters/combine filter outputs
                m, b, var_err, min_freq = fit_filter_combine(jit_params)
                # combine all error sources
                err = combine_errors(m, b, var_err, min_freq, slope)
                # Fit each, use the best fit
                if err < best_err:
                    best_err = err
                    best_params = jit_params
        params = best_params
        print params
        print best_err
        slope += slope_step

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('knees', nargs='+', type=float)

    args = parser.parse_args()

    main(args.knees)
