#!/usr/bin/env python
################################################################################
# Mess around with different ways to move filters around

import argparse
import math
import numpy

from characteristics import filter_characteristics
from libnoisEE import *
from filter_ev import ideal_filter

def main(path, white, state):
    window_size = 8192

    # Set up the filters
    filters = [state, white]

    # Generate the ideal filter
    ixs, iys = ideal_filter(white, state)
    plt.plot(ixs, iys, label='Ideal')

    # Generate the actual filter
    wav_data = read_wav(path)
    white_spectra = lg_fft(wav_data[:window_size])
    white_level = sum(white_spectra) / len(white_spectra)
    lg_freq, spectra = get_lg_data(wav_data, filters,
                                   truncate_start=window_size * 10,
                                   sample_size=window_size)
    freq = [10**f for f in lg_freq]
    norm_spectra = [s - white_level for s in spectra]
    plt.plot(freq, norm_spectra, label='Actual')

    # Smooth the actual
    smooth_spectra = loess(lg_freq, norm_spectra, width=0.5)
    plt.plot(freq, smooth_spectra, label='Smooth Actual')
    
    plt.xscale('log')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('white', type=float)
    parser.add_argument('state', type=float)

    args = parser.parse_args()

    main(args.path, args.white, args.state)
