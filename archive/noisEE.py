#!/usr/bin/env python
################################################################################
# Script to find families of digital filter parameters that produce arbitrary
# falloff, in pursuit of noise of any color.
################################################################################

import argparse
import copy
import multiprocessing
import numpy
import random
import sys

from libnoiseEE import *

SAMPLE_RATE = 44100

PINK_SLOPE = 10.0
PINK_FILTER = [
    0.99765, 0.0990460,
    0.96300, 0.2965164,
    0.57000, 1.0526913,
    0, 0.1848,
]

################################################################################
# ML

def jitter_params(parameters, parameters_error, step_multiplier=0.01,
                  local_pressure=0):
    # Make a copy of the params, to prevent clobbering
    jittered_params = copy.deepcopy(parameters)
    # Figure how large the error step should be
    pressure_multiplier = step_multiplier * (local_pressure + 1)
    error_step = parameters_error * pressure_multiplier
    # Choose how many params to change, depending on local pressure
    # 0(1, 1/10, 1/100...) -> 100(1, 1/2, 1/4...) -> inf(1, 1, 1...)
    falloff = 1/(8./900. * (local_pressure + 25./2.))
    weights = [1./(falloff + 1.)**i for i in range(len(parameters))]
    rand_weights = sum(weights) * random.random()
    num_params = 0
    for i in range(len(parameters)):
        if rand_weights < sum(weights[:i + 1]):
            num_params = i + 1
            break
    # Choose which indicies to change
    indicies = random.sample(xrange(len(parameters)), num_params)
    # Do a uniform change
    for ind in indicies:
        jittered_params[ind] += error_step * (random.random() - 0.5)
    return jittered_params

def combine_error(target_slope, slope, error,
                  max_slope_error=0.05, max_error=10):
    slope_error = 0
    if abs(slope - target_slope) > max_slope_error:
        slope_error = abs(target_slope - slope)/max_slope_error - 1
    error_error = 0
    if error > max_error:
        # 4 chosen empirically, to speed up convergence
        error_error = 2 * (error/max_error - 1)
    return slope_error + error_error

def hill_climb_worker(wav_data, param_queue, result_queue,
                      max_slope_error=0.05, max_error=10,
                      truncate_start=0, sample_size=1024):
    while True:
        quitp = param_queue.get()
        # Exit condition
        if quitp is None:
            return
        target_slope, params = quitp

        try:
            slope, error = get_filter_slope(wav_data, params,
                                            truncate_start=truncate_start,
                                            sample_size=sample_size)
        except FloatingPointError:
            # Report failure to help signal when all the data is in.
            result_queue.put(None)
            continue
        combined_error = combine_error(target_slope, slope, error,
                                       max_slope_error=max_slope_error,
                                       max_error=max_error)

        result_queue.put((params, slope, error, combined_error))

def parallel_hill_climb(data, target_slope, seed_params,
                        param_queue, result_queue,
                        iteration_cap=1000, spin_cap=100,
                        step_multiplier=0.01, branching_factor=20,
                        max_slope_error=0.05, max_error=10,
                        verbose=False):
    '''
    An algorithm to hill climb to the params that get you the best slope
    '''
    params = seed_params
    param_queue.put((target_slope, seed_params))
    minp_result = result_queue.get()
    minp_params, minp_slope, minp_error, minp_combined_error = minp_result

    if verbose >= 2:
        print 'Start Params: slope({:.3f}:{:.3f}) error({:.3f}:{:.3f})'.format(
            minp_slope, target_slope, minp_error, max_error)

    iter_count = 0
    local_pressure = 0
    while (minp_error > max_error or
           abs(minp_slope - target_slope) > max_slope_error):
        # Keep a lid on the iterations, detect when a target is impossible.
        if iter_count > iteration_cap or local_pressure > spin_cap:
            raise Exception('Algorithm seems stuck, too many iterations?')

        # Make some parameters
        jittered_params = [jitter_params(minp_params, minp_combined_error,
                                         step_multiplier=step_multiplier,
                                         local_pressure=local_pressure)
                           for i in range(branching_factor)]

        # Let the workers at it
        for jparams in jittered_params:
            param_queue.put((target_slope, jparams))

        # Get the results back (include the previous iteration)
        results = [(minp_params, minp_slope, minp_error, minp_combined_error)]
        for i in range(branching_factor):
            r = result_queue.get()
            if r:
                results.append(r)
                if verbose >= 2:
                    _, slope, error, combined_error = r
                    sys.stdout.write("\033[K")
                    print 'Jit[{:2}/{}] S{:2.3f} E{:2.3f} CE{:2.3f}'.format(
                        i+1, branching_factor, slope, error, combined_error),
                    print '\r',
                    sys.stdout.flush()
            else:
                if verbose >= 2:
                    sys.stdout.write("\033[K")
                    print 'Jit[{:2}/{}] Skipping errors'.format(
                        i+1, branching_factor),
                    print '\r',
                    sys.stdout.flush()

        # Find the argmin
        minp_result = min(results, key=lambda r:r[3])

        # Check if the result is stuck, increase the pressure
        if minp_params == minp_result[0]:
            local_pressure += 1
        else:
            local_pressure = 0

        minp_params, minp_slope, minp_error, minp_combined_error = minp_result
        iter_count += 1

        if verbose >= 1:
            print 'Itera[{:3}] S{:.3f} E{:.3f} CE{:2.3f}'.format(
                iter_count, minp_slope, minp_error, minp_combined_error)

            # Force write to file, if redirecting to a file
            sys.stdout.flush()

    return minp_params

################################################################################
# main

def main(wav_path, verbose=False, filter_size=4,
         white_slope=0.0, black_slope=10.0, slope_step=0.1,
         sample_size=1024, truncate_start=0,
         branching_factor=20, iteration_cap=1000, spin_cap=100,
         step_multiplier=0.01, max_slope_error=0.05, max_error=10):
    wav_data = read_wav(wav_path)
    user_assert(len(wav_data) >= sample_size, 'Audio sample not large enough')

    numpy.seterr(all='raise')

    # Start workers
    param_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    process_args = (wav_data, param_queue, result_queue,
                    max_slope_error, max_error, truncate_start, sample_size)
    process_list = [multiprocessing.Process(target=hill_climb_worker,
                                            args=process_args)
                    for i in range(multiprocessing.cpu_count())]
    for proc in process_list:
        proc.start()

    filter_params = [1.0 if i == 1 else 0.0 for i in range(2 * filter_size)]

    # Find the slopes we want
    assert white_slope < black_slope
    slope_steps = numpy.arange(white_slope, black_slope, slope_step)
    for i, target_slope in enumerate(slope_steps):
        print '=================================================='

        # Hill climb over each slope
        filter_params = parallel_hill_climb(wav_data,
                                            target_slope, filter_params,
                                            param_queue, result_queue,
                                            step_multiplier=step_multiplier,
                                            iteration_cap=iteration_cap,
                                            spin_cap=spin_cap,
                                            branching_factor=branching_factor,
                                            max_slope_error=max_slope_error,
                                            max_error=max_error,
                                            verbose=verbose)
        print 'FILTER[{}/{}] (slope: {}):'.format(
            i, len(slope_steps), target_slope)
        for j in range(len(filter_params)/2):
            print '\tb{i} = {c1} * b{i} + {c2} * w'.format(
                i=j, c1=filter_params[2*j], c2=filter_params[2*j+1])

        # Force write to file, if redirecting to a file
        sys.stdout.flush()

    # Shut down workers
    for i in range(len(process_list)):
        param_queue.put(None)
    for proc in process_list:
        proc.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('wavpath', help='')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Turn on verbose debug output.')
    parser.add_argument('-vv', action='store_true',
                        help='Turn on really verbose debug output.')
    parser.add_argument('-f', '--filter-size', type=int, default=4,
                        help='Number of state variables to use')
    parser.add_argument('-u', '--white-slope', type=float, default=0.0,
                        help='White noise falloff (slower falloff) db/oct')
    parser.add_argument('-d', '--black-slope', type=float, default=10.0,
                        help='Blacker noise falloff (faster falloff) db/oct')
    parser.add_argument('-s', '--slope-step', type=float, default=0.1,
                        help='Granularity of the steps between maximization')
    parser.add_argument('--size', '--fft-size', type=int, default=1024,
                        help='Change the size of the FFT sample.')
    parser.add_argument('-t', '--truncate', type=int, default=0,
                        help=('Truncate some samples from filtered audio before'
                              ' getting spectra.'))
    parser.add_argument('-b', '--branch', type=int, default=20,
                        help='How many branches to generate at each iteration.')
    parser.add_argument('-i', '--iter-cap', type=int, default=1000,
                        help='How many iterations to allow before failing.')
    parser.add_argument('-sc', '--spin-cap', type=int, default=100,
                        help='How many spin iterations to allow before failing.')
    parser.add_argument('-sm', '--step-multiplier', type=float, default=0.01,
                        help='How large of a step to allow when jittering.')
    parser.add_argument('-a', '--slope-error', type=float, default=0.05,
                        help='How large of a difference in slope to allow.')
    parser.add_argument('-e', '--max-error', type=float, default=10.0,
                        help='How large of a residual fit error to allow.')

    args = parser.parse_args()

    verbose = 0
    if args.vv:
        verbose = 2
    elif args.verbose:
        verbose = 1

    main(args.wavpath, verbose=verbose, filter_size=args.filter_size,
         white_slope=args.white_slope, black_slope=args.black_slope,
         slope_step=args.slope_step,
         sample_size=args.size, truncate_start=args.truncate,
         branching_factor=args.branch, iteration_cap=args.iter_cap,
         spin_cap=args.spin_cap, step_multiplier=args.step_multiplier,
         max_slope_error=args.slope_error, max_error=args.max_error)
