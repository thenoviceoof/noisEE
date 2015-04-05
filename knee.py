#!/usr/bin/env python
################################################################################
# Investigate what the knee behavior is

import argparse
import math
import matplotlib.pyplot as plt
import os

from libnoisEE import *

def knee_worker(params):
    wav_data, white, state, size = params
    xs, ys = get_lg_data(wav_data, [state, white], sample_size=size,
                         truncate_start=size * 10)
    lys = loess(xs, ys, width=0.5)
    max_y = max(lys)
    for x,y in reversed(zip(xs,lys)):
        if y > max_y - 3:
            break
    return state, 10**x

def test1(wav_data, white=0.1, steps=20, size=1024):
    stops = [(float(i)/steps)**2 for i in range(steps)]
    stops = [1-s for s in stops]

    # Process things in parallel
    proc_pool = multiprocessing.Pool()
    params = [(wav_data, white, s, size) for s in stops]
    res = proc_pool.map(knee_worker, params)
    xms, yms = [r[0] for r in res], [r[1] for r in res]
    return xms, yms

# Poly fit!
def poly_fit(xms, yms, degree, size=1024):
    print '=' * 80
    print 'Degree %d' % degree
    res = numpy.polyfit(xms, yms, degree, full=True)
    coeffs, residuals, rank, sing, rcond = res
    print 'Residuals\t%f' % residuals[0]
    print 'Rank\t%d' % rank
    print 'Rcond\t%f' % rcond

    coeffs = list(reversed(coeffs))
    print coeffs

    sim_xms = [float(j)/size for j in range(size + 1)]
    sim_yms = [sum(coeffs[i] * x**i for i in range(len(coeffs)))
               for x in sim_xms]
    plt.plot(xms, yms, label='data')
    plt.plot(sim_xms, sim_yms, label='fit %d' % degree)
    plt.legend()
    plt.show()

    return coeffs

def main(path, steps=10, degree=4, size=1024, pickle=False):
    try:
        if pickle:
            xms,yms = nct_load()
        else:
            raise NCTLoadException
    except NCTLoadException:
        print 'Generating new data...'
        wav_data = read_wav(path)

        # It turns out white doesn't affect the knee at all
        xms, yms = test1(wav_data, white=0.2, steps=steps, size=size)
        yms = [(y/(SAMPLE_RATE/2)) for y in yms]

        if pickle:
            nct_dump((xms, yms))

    import pprint
    pprint.pprint(zip(xms,[y * SAMPLE_RATE/2 for y in yms]))
    # Throw out extra zeros at the beginning
    wxms = xms
    wyms = yms
    i = -1
    while yms[i] == 1.0:
        i -= 1
    if i < -1:
        wxms = xms[:min(i + 2, -1)]
        wyms = yms[:min(i + 2, -1)]

    # Hmm, looks like a negative log...
    eyms = [1/10**y for y in wyms]
    poly_fit(wxms[:-2], eyms[:-2], 4)  # -2 b/c empir

    yfms = [1/(-0.30146697706424969 +
               3.7248300949823099 * x +
               -5.5472369176016798 * x**2 +
               4.5164881456764085 * x**3 +
               -1.3932002981788807 * x**4) for x in xms]
    gyms = [math.log(fy, 10) if fy > 0 else 5 for fy in yfms]

    plt.plot(wxms, wyms)
    plt.plot(xms, gyms)
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('-s', '--steps', type=int, default=10)
    parser.add_argument('-d', '--degree', type=int, default=4)
    parser.add_argument('-f', '--fft', type=int, default=1024)
    parser.add_argument('--pickle', action='store_true')

    args = parser.parse_args()

    main(args.path, steps=args.steps, degree=args.degree, size=args.fft,
         pickle=args.pickle)
