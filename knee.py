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

def main(paths, steps=10, degree=4):
    wav_data = [read_wav(path) for path in paths]

    ymss = []
    for wd in wav_data:
        # It turns out white doesn't affect the knee at all
        xms, yms = test1(wd, white=0.2, steps=20)
        yms = [(y/22050) for y in yms]
        ymss.append(yms)

    # Make it look like the X is backwards
    xms = [1.-x for x in xms]
    for yms in ymss:
        plt.plot(xms, yms)

    # Poly fit!
    yms = [sum(ys)/len(wav_data) for ys in numpy.transpose(ymss)]
    res = numpy.polyfit(xms, yms, degree, full=True)
    coeffs, residuals, rank, sing, rcond = res
    print 'Residuals\t%f' % residuals[0]
    print 'Rank\t%d' % rank
    print 'Rcond\t%f' % rcond

    coeffs = list(reversed(coeffs))
    print coeffs

    yms = [sum(coeffs[i] * x**i for i in range(len(coeffs))) for x in xms]
    plt.plot(xms, yms)

    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+')
    parser.add_argument('-s', type=int, default=10)
    parser.add_argument('-d', type=int, default=4)

    args = parser.parse_args()

    main(args.paths, steps=args.s, degree=args.d)
