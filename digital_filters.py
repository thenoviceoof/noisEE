#!/usr/bin/env python

import argparse
import array
import copy
import hashlib
import math
import multiprocessing
import numpy
from numpy import fft
import random
import os.path
import pickle
import sys
import wave

from libnoisEE import *

################################################################################
# audio manipulation

def to_fp(from_range, to_range, value):
    bot, top = from_range
    frac = (value - bot)/(top - bot)
    return int(to_range[0] + (to_range[1] - to_range[0]) * frac)
def from_fp(from_range, to_range, value):
    bot, top = to_range
    frac = float(value - bot)/(top - bot)
    return int(from_range[0] + (from_range[1] - from_range[0]) * frac)

def apply_digital_filter(params, data, in_bits=12, out_bits=10, int_bits=16):
    '''
    Apply a "real" digital filter to a signal
    '''
    assert len(params) % 2 == 0
    prev_coeff = params[::2]
    mix_coeff = params[1::2]
    assert len(prev_coeff) == len(mix_coeff)
    coeff_count = len(prev_coeff)

    zero = to_fp([-1, 1], [-2**(int_bits-1), 2**(int_bits-1)-1], 0.0)
    # convert coeffs to fixed point
    prev_coeff = [to_fp([-1, 1], [-2**(int_bits-1), 2**(int_bits-1)-1], p)
                  for p in prev_coeff]
    mix_coeff = [to_fp([-1, 1], [-2**(int_bits-1), 2**(int_bits-1)-1], p)
                 for p in mix_coeff]

    intb = sum(1<<i for i in range(int_bits))
    filter_state = [zero for i in range(coeff_count)]
    filtered_data = []
    for d in data:
        # zero out the necessary in bits
        if in_bits < int_bits:
            d = d & (~sum([1<<i for i in range(int_bits - in_bits)]))
        filter_state = [prev_coeff[i]*filter_state[i] + mix_coeff[i]*d
                        for i in range(coeff_count)]
        filter_state = [s >> (int_bits - 1) for s in filter_state]
        # make sure only int_bits survive
        filter_state = [s & intb if s > 0 else -((-s) & intb)
                        for s in filter_state]
        filter_out = sum(filter_state)
        out = max(min(filter_out, 2**(int_bits-1)-1), -2**(int_bits-1))
        # zero out the necessary out bits
        if out_bits < int_bits:
            out = out & (~sum([1<<i for i in range(int_bits - out_bits)]))
        filtered_data.append(out)
    return filtered_data

def write_wav(path, data):
    wav_file = wave.open(path, 'w')

    wav_file.setnchannels(1)
    wav_file.setframerate(SAMPLE_RATE)
    wav_file.setsampwidth(2)

    # Convert from byte(s) array to string
    arr = array.array('h')
    arr.fromlist(data)

    wav_file.writeframes(arr.tostring())

def main(in_path, out_path, params, in_bits=12, out_bits=10, int_bits=16):
    wav_data = read_wav(in_path)
    filter_data = apply_digital_filter(params, wav_data, int_bits=int_bits,
                                       in_bits=in_bits, out_bits=out_bits)
    write_wav(out_path, filter_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('in_path')
    parser.add_argument('out_path')
    parser.add_argument('params', nargs='+', type=float)
    parser.add_argument('--int', type=int, default=16)
    parser.add_argument('--in', type=int, default=12, dest='in_bits')
    parser.add_argument('--out', type=int, default=10)

    args = parser.parse_args()

    main(args.in_path, args.out_path, args.params, int_bits=args.int,
         in_bits=args.in_bits, out_bits=args.out)
