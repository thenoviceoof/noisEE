#!/usr/bin/env python
################################################################################
# Investigate what the knee behavior is

import argparse
import math
import matplotlib.pyplot as plt

from libnoisEE import *

def test1(wav_data, white=0.1, steps=20):
    stops = [float(i)/steps for i in range(steps)]
    fils = [[1-s, white] for s in stops]

    fil_data = [get_lg_data(wav_data, fil, sample_size=1024) for fil in fils]
    xs = fil_data[0][0]
    fil_data = [fd[1] for fd in fil_data]

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
            yms.append(-100)
    return xms, yms

def main(paths, steps=10):
    wav_data = [read_wav(path) for path in paths]

    ########################################
    # make some filters
    stops = [float(i)/steps for i in range(steps)]
    #stops = [(float(steps-i)/steps)**2 for i in range(steps)]
    #stops = [1./(2**i) for i in range(steps)]
    
    # log exchange - equal spacing at const falloff
    #stops = [1./(4**(steps-i)) for i in range(steps)]
    #fils = [[1-s, s] for s in stops]

    stops = [float(i)/steps for i in range(steps)]
    fils = [[1-s, 0.1] for s in stops]

    # Trying things
    # fils = [(0.96300, 0.296514)]

    ########################################
    # prep the data
    # fil_data = [get_lg_data(wav_data, fil) for fil in fils]
    # xs = fil_data[0][0]
    # fil_data = [fd[1] for fd in fil_data]

    ########################################
    # display the data
    # for fdata in fil_data:
    #     plt.plot(xs, fdata)
    # plt.show()

    xms, yms = test1(wav_data, white=0.2, steps=20)
    yms = [(y/22050) for y in yms]
    #yms = [ for y in yms]
    #plt.plot(xms, yms)

    # yms  = [1/((1.8*x+1)**3) for x in xms]
    #coeff = 30.
    #yms = [(coeff**((1-x)) - 1)/(coeff-1.) for x in xms]
    xms = [1.-x for x in xms]
    plt.plot(xms, yms)
    res = numpy.polyfit(xms, yms, 4, full=True)
    coeffs, residuals, rank, sing, rcond = res
    print 'Residuals\t%f' % residuals[0]
    print 'Rank\t%d' % rank
    print 'Rcond\t%f' % rcond
    #print residuals, rank, sing, rcond
    coeffs = list(reversed(coeffs))
    print coeffs
    # yms = [0.2*(1-x)+0.8*(1-x)**4 for x in xms]
    yms = [sum(coeffs[i] * x**i for i in range(len(coeffs))) for x in xms]
    plt.plot(xms, yms)

    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-s', type=int, default=10)

    args = parser.parse_args()

    main(args.paths, steps=args.s)
