#!/usr/bin/env python
################################################################################
# Mess around with different ways to move filters around

import argparse
import math
import numpy

from characteristics import filter_characteristics
from libnoisEE import *
from filter_ev import ideal_filter

from digital_filters import apply_digital_filter

def main(path, white, state, find_knee=False, floating=False, digital=False,
         in_bits=12, out_bits=10, int_bits=16):
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

    if floating:
        lg_freq, spectra = get_lg_data(wav_data, filters,
                                       truncate_start=window_size * 10,
                                       sample_size=window_size)
        freq = [10**f for f in lg_freq]
        norm_spectra = [s - white_level for s in spectra]
        plt.plot(freq, norm_spectra, label='Actual', alpha=0.5)

        # Smooth the actual
        smooth_spectra = loess(lg_freq, norm_spectra, width=0.5)
        plt.plot(freq, smooth_spectra, label='Smooth Actual')

        if find_knee:
            m_s = max(smooth_spectra)
            for x,s in reversed(zip(freq, smooth_spectra)):
                if s > m_s - 3:
                    print m_s
                    print s
                    print x
                    break

    # Generate the digital filter
    if digital:
        def app_filter(params, data):
            return apply_digital_filter(params, data,
                                        in_bits=in_bits, out_bits=out_bits,
                                        int_bits=int_bits)
        _, spectra = get_lg_data(wav_data, filters,
                                 truncate_start=window_size * 10,
                                 sample_size=window_size,
                                 filter_fn=app_filter)
        norm_spectra = [s - white_level for s in spectra]
        plt.plot(freq, norm_spectra, label='Actual Digital', alpha=0.5)

        # Smooth the digital filter
        smooth_spectra = loess(lg_freq, norm_spectra, width=0.5)
        plt.plot(freq, smooth_spectra, label='Smooth Actual Digital')
    
    plt.xscale('log')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('white', type=float)
    parser.add_argument('state', type=float)
    parser.add_argument('-f', '--floating', action='store_true')
    parser.add_argument('-d', '--digital', action='store_true')
    parser.add_argument('-k', '--knee', action='store_true')
    parser.add_argument('--in-bits', type=int, default=12)
    parser.add_argument('--out-bits', type=int, default=10)
    parser.add_argument('--int-bits', type=int, default=16)

    args = parser.parse_args()

    main(args.path, args.white, args.state, floating=args.floating,
         digital=args.digital, find_knee=args.knee,
         in_bits=args.in_bits, out_bits=args.out_bits, int_bits=args.int_bits)
