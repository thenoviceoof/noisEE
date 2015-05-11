#!/usr/bin/env python
################################################################################
# Calculate the passband functions given knees

import argparse
import math
import numpy

from multiprocessing import Pool

from characteristics import filter_characteristics
from libnoisEE import *

import itertools

FLOATING_POINT_EPSILON = 1e-4

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
    org_err = abs(m * min_freq - b)
    slp_err = abs(m - slope)
    #  1 / 1 / 10 bc fine grained slope
    err = 1 * var_err + 1 * org_err + 100 * slp_err
    return err

def passband_worker(params):
    try:
        jit_params, slope = params
        # apply filters/combine filter outputs
        m, b, var_err, min_freq = fit_filter_combine(jit_params)
        # combine all error sources
        err = combine_errors(m, b, var_err, min_freq, slope)
        return m, b, err, jit_params
    except KeyboardInterrupt:
        # Allow quitting out of pools with a keyboard interrupt
        pass
    except ValueError:
        # Catch and ignore math domain errors (negative log)
        pass

def find_passbands(worker_pool, slope, params):
    # preseed with random elements
    print 'Finding preseed...'
    slopes = [p[0] for p in params]
    random_dbs = []
    while len(random_dbs) < 10000:
        dbs = [random.uniform(0, -80) for j in range(len(params))]
        if all(x + 10 > y for x,y in zip(dbs,dbs[1:])):
            random_dbs.append(dbs)
    random_params = ((list(zip(slopes, p)), slope) for p in random_dbs)
    grid_output = worker_pool.map(passband_worker, random_params)
    _, _, best_err, best_params = min((g for g in grid_output if g),
                                      key=lambda a: a[2])
    if best_err > passband_worker((params, slope))[2]:
        best_params = params
    else:
        print 'Found better starting parameters'
        sys.stdout.flush()

    m, b, var_err, min_freq = fit_filter_combine(params)
    best_err = combine_errors(m, b, var_err, min_freq, slope)
    best_m, best_b = m, b

    itr_count = 0
    pressure, pressurep = 0, False
    # Keep on looking while we don't have the best fit
    while ((best_err > 2 or pressure < 20) and
           not (itr_count > 200 and best_err < 5) and
           not (itr_count > 9998)):
        # Generate list of tweaked passbands
        jit_param_list = []
        for j in range(100):
            width = 0.2 * best_err + 0.05 * pressure**2
            jit_params = [[s,p + random.gauss(0, width)] for s,p in best_params]
            jit_param_list.append((jit_params, slope))
        # Release the workers
        output = worker_pool.map(passband_worker, jit_param_list)
        m, b, err, jit_params = min((g for g in output if g), key=lambda a: a[2])
        if err < best_err:
            best_m, best_b = m, b
            best_err = err
            best_params = jit_params
        # Add pressure if we're not more than a tiny bit better
        if err > best_err - FLOATING_POINT_EPSILON:
            pressurep = True

        itr_count += 1
        # Pressure the optimizer / check if this is the best outcome
        if pressurep:
            pressure += 1
            pressurep = False
        else:
            pressure = 0
        # yield, to allow the main loop to output things
        yield best_params, best_err, best_m, best_b, itr_count
    yield best_params, best_err, best_m, best_b, itr_count

def main(knees, slope_step=-0.1, slope_start=0.0, slope_end=-6.0):
    numpy.seterr(over='ignore')

    # grab any previous writes
    try:
        data_file = open('analog_characteristic.log')
        data = pickle.load(data_file)
        data_file.close()
    except IOError:
        # for accumulating data into (slope, params)
        data = {}

    log_file = open('analog_characteristic.log', mode='w')
    log_file.write(pickle.dumps(data))
    log_file.flush()

    # make sure knees are smallest->largest
    knees = sorted(knees)
    # make sure there's a "white noise" source
    if knees[-1] < SAMPLE_RATE/2:
        knees.append(4 * SAMPLE_RATE)

    # init the filters to super soft, except for white
    params = [[knee, -100.0] for knee in knees]
    params[-1][1] = 0.0
    # make sure the slope steps and start/end agree
    assert slope_end < slope_start
    assert slope_step < 0
    # Make a worker pool, allow quitting gracefully from it
    worker_pool = Pool()
    try:
        # For each slope...
        slope = slope_start
        while slope >= slope_end:
            # skip if we've already calculated
            if slope in data:
                params = [p for _,p in data[slope]]
                slope += slope_step
                continue

            print '=' * 80
            print 'Slope target: {:.5}'.format(slope)

            passband_generator = find_passbands(worker_pool, slope, params)
            for params, err, m, b, itr_count in passband_generator:
                # Print best guess
                sys.stdout.write('\r' + (' ' * 82))
                param_str = ','.join(["{:.3}".format(p) for _,p in params])
                out_str = "\r[{:4}] Err {:.5} Param {} m/b {:.3}/{:.3}".format(
                    itr_count + 1, err, param_str, m, b)
                sys.stdout.write(out_str)
                sys.stdout.flush()
                # Save the outputs for stdout every once in a while
                itr_count += 1
                if itr_count % 100 == 0:
                    print ""
            else:
                print ""
            # Print the best param/final error
            print params
            print err
            # Accumulate params, write out
            data[slope] = list(zip(knees, params))
            log_file.seek(0)
            log_file.write(pickle.dumps(data))
            log_file.flush()
            slope += slope_step
    except KeyboardInterrupt:
        print ''
        print 'ABORTING...'
        worker_pool.close()
        print 'ABORT COMPLETE'
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('knees', nargs='+', type=float)

    args = parser.parse_args()

    main(args.knees)
