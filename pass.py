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

    fil_data = [smooth(fd) for fd in fil_data]

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

    plt.plot(xms, yms)
    genx = [i/1024. for i in range(1024 + 1)]
    geny = [sum([coeffs[i] * x**i for i in range(degree+1)]) for x in genx]
    plt.plot(genx, geny)
    plt.title('Degree %d' % degree)
    plt.show()

def main(path, steps=10, degree=4, print_poly=False, print_log_slope=False):
    wav_data = read_wav(path)

    white_data = get_lg_data(wav_data, [0.0, 1.0], sample_size=1024)
    white_level = sum(white_data[1])/len(white_data[0])

    # X - white param, Y - state param, Z - steady state db
    #xms = [float(i+1)/steps for i in range(steps)]
    xms = [1./2.**i for i in range(steps)]
    ps = []
    for x in xms:
        yms, zms = test1(wav_data, white=x, steps=steps)
        zms = [z - white_level for z in zms]
        for y,z in zip(yms, zms):
            ps.append((x, y, z))

    ux = sorted(list(set([x for x,y,z in ps])))
    uy = sorted(list(set([y for x,y,z in ps])))

    if print_log_slope:
        print '=' * 80
        print 'log slope (lg2)'
        xms = [x for x,y,z in ps if y == 0]
        zms = [z for x,y,z in ps if y == 0]
        # normalize
        mz = max(zms)
        zms = [z - mz for z in zms]
        ams = [z/math.log(x, 2) for x,z in zip(xms, zms) if x != 1.0]
        print ams
        print sum(ams)/len(ams)

    # Find the polynomials that fit both X/Z and Y/Z graphs
    if print_poly:
        print '=' * 80
        print 'State vs DB'
        cx = ux[len(ux)/2]
        yms = [y for x,y,z in ps if x == cx]
        zms = [z for x,y,z in ps if x == cx]
        print ''
        print '@ degree %d @ x == %f' % (degree - 1, cx)
        print_polyfit(yms, zms, degree - 1)
        print ''
        print '@ degree %d @ x == %f' % (degree, cx)
        print_polyfit(yms, zms, degree)
        print ''
        print '@ degree %d @ x == %f' % (degree + 1, cx)
        print_polyfit(yms, zms, degree + 1)
        print ''
        print '@ degree %d @ x == %f' % (degree + 2, cx)
        print_polyfit(yms, zms, degree + 2)

    # Subplot X/Z and Y/Z
    plt.subplot(2, 1, 1)
    for cy in uy:
        xms = [x for x,y,z in ps if y == cy]
        zms = [z for x,y,z in ps if y == cy]
        plt.plot(xms, zms, label='%f' % cy)
    plt.legend()

    plt.subplot(2, 1, 2)
    for cx in ux:
        yms = [y for x,y,z in ps if x == cx]
        zms = [z for x,y,z in ps if x == cx]
        plt.plot(yms, zms, label='%f' % cx)
    plt.legend()

    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('-s', '--steps', type=int, default=10)
    parser.add_argument('-d', '--degree', type=int, default=3)
    parser.add_argument('-p', '--print', action='store_true', dest='pprint')
    parser.add_argument('-l', '--print-log-slope', action='store_true')

    args = parser.parse_args()

    main(args.path, steps=args.steps, degree=args.degree,
         print_poly=args.pprint, print_log_slope=args.print_log_slope)
