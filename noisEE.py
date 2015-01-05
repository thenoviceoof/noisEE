#!/usr/bin/env python
################################################################################
# Script to find families of digital filter parameters that produce arbitrary
# falloff, in pursuit of noise of any color.
################################################################################

import argparse
import array
import math
import numpy
from numpy import fft
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

def fft_db(wav_data):
    '''
    Returns the FFT data, scaled as if destined for a log-log graph
    '''
    norm_data = [float(d) / (2**15) for d in wav_data]
    fft_data_complex = fft.rfft(norm_data)
    fft_data = numpy.absolute(fft_data_complex) / len(fft_data_complex)
    fft_data_lg = 20 * numpy.log10(fft_data)

    return fft_data_lg

################################################################################
# ML

def get_slope(lg_freq, spectrum):
    '''
    Find the slope/error of the frequency spectrum
    '''
    fit, error, _, _, rcond = numpy.polyfit(lg_freq, spectrum, 1, full=True)
    m, b = fit
    return m, error[0]**0.5

################################################################################
# main

def main(wav_path, sample_size=1024, display_spectra=False):
    wav_data = read_wav(wav_path)
    user_assert(len(wav_data) >= sample_size, 'Audio sample not large enough')

    # Split the data into a bunch of sample_size arrays
    wav_data = [wav_data[i*sample_size:(i+1)*sample_size]
                for i in range(len(wav_data)/sample_size)]

    # Apply the fft to each bucket, and average the frequency spectrums
    spectra = [fft_db(wd) for wd in wav_data]
    spectra_avg = sum(spectra) / len(spectra)

    # Join the spectra data (x) with the log frequency (y),
    # for a true lg-lg plot, removing the constant (to avoid -inf)
    freq = fft.rfftfreq(sample_size, 1.0/SAMPLE_RATE)[1:]
    lg_freq = numpy.log10(freq)
    spectra_avg = spectra_avg[1:]

    if display_spectra and plt:
        plt.plot(freq, spectra_avg)
        plt.xscale('log')
        plt.show()

    # Find slope of falloff for data
    slope, error = get_slope(lg_freq, spectra_avg)

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
