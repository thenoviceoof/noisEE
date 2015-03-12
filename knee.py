#!/usr/bin/env python
################################################################################
# Investigate what the knee behavior is

import argparse
import math
import matplotlib.pyplot as plt

from libnoisEE import *

def test1(wav_data, white=0.1, steps=20):
    stops = [(float(i)/steps)**2 for i in range(steps)]
    fils = [[1-s, white] for s in stops]

    fil_data = [get_lg_data(wav_data, fil, sample_size=4196) for fil in fils]
    xs = fil_data[0][0]
    fil_data = [fd[1] for fd in fil_data]

    # Smooth out the data to get better knee calculations
    fil_data = [smooth(fd) for fd in fil_data]

    maxes = [max(fd) for fd in fil_data]
    xms = []; yms = []
    for j, dd in enumerate(zip(maxes, fil_data)):
        mfd, fd = dd
        for i, d in enumerate(fd):
            if d < mfd - 3:
                print 10**xs[i],
                print '\t',
                print fils[j]
                xms.append(fils[j][0])
                yms.append(10**xs[i])
                break
        else:
            xms.append(fils[j][0])
            yms.append(SAMPLE_RATE/2)
    return xms, yms

def main(path, steps=10, degree=4):
    wav_data = read_wav(path)

    # It turns out white doesn't affect the knee at all
    xms, yms = test1(wav_data, white=0.2, steps=steps)
    yms = [(y/22050) for y in yms]

    # Subtract out the obvious inverse component
    in_yms = [(0.04 / x if x > 0.04 else 1.0) for x in xms]
    syms = [y - iy for iy,y in zip(in_yms,yms)]

    plt.plot(xms, yms)
    plt.plot(xms, syms)
    plt.show()

    # Poly fit!
    def poly_fit(xms, yms, degree):
        print '=' * 80
        print 'Degree %d' % degree
        res = numpy.polyfit(xms, yms, degree, full=True)
        coeffs, residuals, rank, sing, rcond = res
        print 'Residuals\t%f' % residuals[0]
        print 'Rank\t%d' % rank
        print 'Rcond\t%f' % rcond

        coeffs = list(reversed(coeffs))
        print coeffs

        sim_xms = [float(j)/1024. for j in range(1024 + 1)]
        sim_yms = [sum(coeffs[i] * x**i for i in range(len(coeffs)))
                   for x in sim_xms]
        plt.plot(xms, yms, label='data')
        plt.plot(sim_xms, sim_yms, label='fit %d' % degree)
        plt.legend()
        plt.show()

    poly_fit(xms[:-4], syms[:-4], degree)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('-s', type=int, default=10)
    parser.add_argument('-d', type=int, default=4)

    args = parser.parse_args()

    main(args.path, steps=args.s, degree=args.d)
