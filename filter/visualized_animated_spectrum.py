################################################################################
## Copyright 2017 "Nathan Hwang" <thenoviceoof>
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
################################################################################

import csv
import math
import matplotlib
import matplotlib.pyplot as plt

# Draw the spectrum gif used in the blog.

SAMPLING_FREQUENCY = 44100
SAMPLING_PERIOD = 1.0/SAMPLING_FREQUENCY

def even_log_frequencies(n=200, low_frequency=20, high_frequency=20000):
    high_log = math.log(high_frequency, 10)
    low_log = math.log(low_frequency, 10)
    logs = [(high_log - low_log)*(float(i)/n)+low_log for i in range(n)]
    return [10**l for l in logs]

def transfer_function(f_c, gain, frequencies, sampling_period=SAMPLING_PERIOD):
    p = 2 * math.pi * sampling_period * f_c
    previous_output_coefficient = 1/(p + 1)
    input_coefficient = gain - 1/p
    frequency_response = [math.e**(-2*math.pi*f*sampling_period*1j) for f in frequencies]
    gains = [abs(input_coefficient * fr) / abs(1 + previous_output_coefficient * fr)
             for fr in frequency_response]
    return gains

def gain_function(f_c, gain, frequencies, sampling_period=SAMPLING_PERIOD):
    '''Returns the power gain for a frequency'''
    # A = 1/(1+f/f_c), power is |A|^2 = 1/sqrt(1+(f/f_c)^2)^2
    gains = [gain/((f/f_c)**2 + 1) for f in frequencies]
    return gains

def sum_gains_power(gains):
    return [10*math.log(sum(gs)/1.0, 10) for gs in zip(*gains)]

# Generate evenly spaced frequencies on a log scale.
frequencies = even_log_frequencies(n=200)

# Use a white figure background.
matplotlib.rcParams['figure.facecolor'] = 'white'

################################################################################
# Read in the functions.
params = {}
with open('linear_parameters.csv') as file:
    csv_file = csv.reader(file, delimiter=',')
    for row in csv_file:
        if row[0] == '':
            continue
        name = row[0].split(' ')[0].lower()
        values = [float(v) for v in row[1:]]
        paired_values = zip(values[:8], values[8:])
        params[name] = paired_values

################################################################################
# Generate (gain/f_c)s for a given slope.

def slope_to_parameters(params, slope):
    fc_gain = [[2000000, None], [16.5, None], [270.0, None], [5300.0, None]]
    index_dict = {
        'constant': 0,
        'low': 1,
        'medium': 2,
        'high': 3,
    }

    # Convert the slope to a target gain.
    for name, linear_fn in params.iteritems():
        max_gain = max([g for _,g in linear_fn])
        gain = None
        for i in range(len(linear_fn)-1):
            if linear_fn[i][0] <= slope < linear_fn[i+1][0]:
                frac = (slope - linear_fn[i][0])/(linear_fn[i+1][0] - linear_fn[i][0])
                gain = linear_fn[i][1] * (1 - frac) + linear_fn[i+1][1] * frac
                break
        if gain is None:
            gain = linear_fn[-1][1]
        # Snap to the nearest potentiometer step.
        if gain < 0:
            gain = 0
        steps = 1024
        gain = math.floor(steps*gain/max_gain)/steps * max_gain
        gain = max(gain, 0.0000000001)
        fc_gain[index_dict[name]][1] = gain

    return fc_gain

max_slope = 0
min_slope = -20

points = 40
for i in range(points+1):
    slope = float(max_slope - min_slope)*(float(i)/(points)) + min_slope
    parameters = slope_to_parameters(params, slope)
    print slope

    all_filters = []
    for fc,gain in parameters:
        transfer_fn = gain_function(fc, gain, frequencies)
        plt.semilogx(frequencies, sum_gains_power([transfer_fn]), color='grey')
        all_filters.append(transfer_fn)
    plt.semilogx(frequencies, sum_gains_power(all_filters),
                 label='Slope %0.1fdb/octave' % slope)
    axes = plt.gca()
    axes.set_xlabel('Log Frequency (Hz)')
    axes.set_ylabel('Aural Power (dB)')

    plt.grid(True)
    plt.legend()
    plt.ylim([-40, 10])
    plt.savefig('filter_fn_{:04.1f}.png'.format(abs(slope)), bbox_inches='tight')

    plt.close()
