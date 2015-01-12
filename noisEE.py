#!/usr/bin/env python
################################################################################
# Script to find families of digital filter parameters that produce arbitrary
# falloff, in pursuit of noise of any color.
################################################################################

import argparse
import array
import copy
import math
import numpy
from numpy import fft
import random
import sys
import wave

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

SAMPLE_RATE = 44100

PINK_SLOPE = 10.0
PINK_FILTER = [
    0.99765, 0.0990460,
    0.96300, 0.2965164,
    0.57000, 1.0526913,
    0, 0.1848
]

################################################################################
# utilities

def user_assert(condition, message):
    '''
    A more user-friendly (no stack traces) way to check data for coherency.
    '''
    if not condition:
        print 'ERROR: %s' % message
        sys.exit(1)

################################################################################
# audio manipulation

def read_wav(path):
    wav_file = wave.open(path)

    user_assert(wav_file.getnchannels() == 1, 'Expect monochannel audio')
    user_assert(wav_file.getframerate() == SAMPLE_RATE, 'Expect 44.1k audio')
    user_assert(wav_file.getsampwidth() == 2, 'Expected signed 16 bit audio')

    data_string = wav_file.readframes(wav_file.getnframes())

    # Convert the data from string to byte(s) array
    data = array.array('h')
    data.fromstring(data_string)

    return list(data)

def fft_db(wav_data):
    '''
    Returns the FFT data, scaled as if destined for a log-log graph
    '''
    norm_data = [float(d) / (2**15) for d in wav_data]
    fft_data_complex = fft.rfft(norm_data)
    fft_data = numpy.absolute(fft_data_complex) / len(fft_data_complex)
    fft_data_lg = 20 * numpy.log10(fft_data)

    return fft_data_lg

def apply_filter(params, data):
    '''
    Apply a digital filter to a signal
    '''
    assert len(params) % 2 == 0
    prev_coeff = params[::2]
    mix_coeff = params[1::2]
    assert len(prev_coeff) == len(mix_coeff)
    coeff_count = len(prev_coeff)

    filter_state = [0 for i in range(coeff_count)]
    filtered_data = []
    for d in data:
        filter_state = [prev_coeff[i]*filter_state[i] + mix_coeff[i]*d
                        for i in range(coeff_count)]
        filtered_data.append(sum(filter_state))
    return filtered_data

def get_slope(lg_freq, spectrum):
    '''
    Find the slope/error of the frequency spectrum
    '''
    fit, error, _, _, rcond = numpy.polyfit(lg_freq, spectrum, 1, full=True)
    m, b = fit
    return m, error[0]**0.5

def get_filter_slope(data, filter_params, truncate_start=0, sample_size=1024):
    # Apply the filter
    data = apply_filter(filter_params, data)

    # Throw data away from the beginning, for better filter data
    data = data[truncate_start:]

    # Split the data into a bunch of sample_size arrays
    data = [data[i*sample_size:(i+1)*sample_size]
            for i in range(len(data)/sample_size)]

    # Apply the fft to each bucket, and average the frequency spectrums
    spectra = [fft_db(wd) for wd in data]
    spectra_avg = sum(spectra) / len(spectra)

    # Generate the log frequency (y) for the spectra data (x),
    # for a true lg-lg plot, removing the constant (to avoid -inf)
    freq = fft.rfftfreq(sample_size, 1.0/SAMPLE_RATE)[1:]
    lg_freq = numpy.log10(freq)
    spectra_avg = spectra_avg[1:]

    slope, error = get_slope(lg_freq, spectra_avg)
    return slope, error

################################################################################
# ML

def jitter_params(parameters, parameters_error, step_multiplier=0.01):
    '''
    '''
    jittered_params = copy.copy(parameters)
    error_step = parameters_error * step_multiplier
    index = random.randint(0, len(jittered_params) - 1)
    jittered_params[index] += error_step * (random.random() - 0.5)
    return jittered_params

def combine_error(target_slope, slope, error,
                  max_slope_error=0.05, max_error=10):
    return (target_slope - slope)/max_slope_error + error/max_error

def hill_climb(data, target_slope, seed_params,
               max_slope_error=0.05, max_error=10,
               step_multiplier=0.01, branching_factor=20, iteration_cap=1000,
               truncate_start=0, sample_size=1024, verbose=False):
    '''
    An algorithm to hill climb to the params that get you the best slope
    '''
    params = seed_params
    slope, error = get_filter_slope(data, params,
                                    truncate_start=truncate_start,
                                    sample_size=sample_size)
    if verbose:
        print 'Starting Parameters: slope({:.3f}:{:.3f}) error({:.3f})'.format(
            slope, target_slope, error)
    combined_error = combine_error(target_slope, slope, error,
                                   max_slope_error=max_slope_error,
                                   max_error=max_error)
    iter_count = 0
    while error > max_error and abs(slope - target_slope) > max_slope_error:
        max_params, max_params_combined_error = params, combined_error
        max_params_slope, max_params_error = slope, error
        # Generate a bunch of jittered params
        for i in range(branching_factor):
            jittered_params = jitter_params(params, combined_error,
                                            step_multiplier=step_multiplier)
            # Figure out the param's fit
            slope, error = get_filter_slope(data, jittered_params,
                                            truncate_start=truncate_start,
                                            sample_size=sample_size)
            if verbose:
                print 'Jit[{: 2}/{}] S{:.3f} E{:.3f}'.format(
                    i, branching_factor, slope, error),
                print '\r',
            # Find the argmax
            combined_error = combine_error(target_slope, slope, error,
                                           max_slope_error=max_slope_error,
                                           max_error=max_error)
            if (max_params_combined_error is None or
                combined_error < max_params_error):
                max_params = jittered_params
                max_params_combined_error = combined_error
                max_params_slope = slope
                max_params_error = error
        params = max_params
        iter_count += 1

        if verbose:
            print 'Iter[{: 3}] S{:.3f} E{:.3f}'.format(
                iter_count, max_params_slope, max_params_error)
    return params

################################################################################
# main

def main(wav_path, sample_size=1024, display_spectra=False):
    wav_data = read_wav(wav_path)
    user_assert(len(wav_data) >= sample_size, 'Audio sample not large enough')

    print hill_climb(wav_data, -10, PINK_FILTER, verbose=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('wavpath', help='')
    parser.add_argument('--fft-size', type=int, default=1024, help='')
    parser.add_argument('--display', action='store_true', help='')

    args = parser.parse_args()

    # If a display is asked for, make sure we can provide one
    user_assert(plt if args.display else True,
                'matplotlib is not installed, cannot display')
    user_assert(2**int(math.log(args.fft_size, 2)) == args.fft_size,
                'FFT sample size should be a power of 2')

    main(args.wavpath, sample_size=args.fft_size, display_spectra=args.display)
