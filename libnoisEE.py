#!/usr/bin/env python

import argparse
import array
import copy
import math
import multiprocessing
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

def log_fft(wav_data):
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
