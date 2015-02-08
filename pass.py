#!/usr/bin/env python
################################################################################
# Investigate what the knee behavior is

import argparse
import math
import matplotlib.pyplot as plt

from libnoisEE import *

def test1(wav_data, white=0.1, steps=20):
    stops = [float(i)/steps for i in range(steps)]
    fils = [[s, white] for s in stops]

    fil_data = [get_lg_data(wav_data, fil, sample_size=1024) for fil in fils]
    xs = fil_data[0][0]
    fil_data = [fd[1] for fd in fil_data]

    maxes = [max(fd) for fd in fil_data]
    return (stops, maxes)

def print_polyfit(xms, yms, degree):
    res = numpy.polyfit(xms, yms, degree, full=True)
    coeffs, residuals, rank, sing, rcond = res
    print 'Residuals\t%f' % residuals[0]
    print 'Rank\t%d' % rank
    print 'Rcond\t%f' % rcond

    coeffs = list(reversed(coeffs))
    print coeffs

def main(path, steps=10, degree=4, const_white=False, const_accum=False):
    wav_data = read_wav(path)

    white_data = get_lg_data(wav_data, [0.0, 1.0], sample_size=1024)
    white_level = sum(white_data[1])/len(white_data[0])

    ymss = []
    for i in (range(1) if const_white else range(steps)):
        if const_white:
            stop = 0.5
        else:
            stop = float(i+1)/steps
        xms, yms = test1(wav_data, white=stop, steps=steps)
        yms = [y - white_level for y in yms]
        ymss.append(yms)

    for yms in ymss:
        plt.plot(xms, yms)

    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('-s', '--steps', type=int, default=10)
    parser.add_argument('-w', '--const-white', action='store_true')
    parser.add_argument('-a', '--const-accum', action='store_true')
    parser.add_argument('-d', '--degree', type=int, default=4)

    args = parser.parse_args()

    main(args.path, steps=args.steps, degree=args.degree,
         const_white=args.const_white, const_accum=args.const_accum)
