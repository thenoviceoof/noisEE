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

import math
import matplotlib.pyplot as plt
from pprint import pprint

# Draw the summed transfer functions for a given family of curves.
#

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
    # print previous_output_coefficient
    # print input_coefficient
    # pprint(frequency_response)
    gains = [abs(input_coefficient * fr) / abs(1 + previous_output_coefficient * fr)
             for fr in frequency_response]
    return gains

def gain_function(f_c, gain, frequencies, sampling_period=SAMPLING_PERIOD):
    gains = [gain/(f/f_c + 1) for f in frequencies]
    return gains

SMALL_GAIN = 0.00001
WHITE_PARAMS = [
    (2000000,  1.0),
    (16.5,   SMALL_GAIN),
    (270.0,  SMALL_GAIN),
    (5300.0, SMALL_GAIN),
]
SCALE = 0.1
PINK_PARAMS = [
    (2000000,  0.1848 * SCALE),
    (16.5,     42.0 * SCALE),
    (270.0,    8.0 * SCALE),
    (5300.0,   2.5 * SCALE),
]
RED_PARAMS = [
    (2000000,  SMALL_GAIN),
    (16.5,   7.0),
    (270.0,  SMALL_GAIN),
    (5300.0, SMALL_GAIN),
]

# Generate evenly spaced frequencies on a log scale.
frequencies = even_log_frequencies(n=200)

################################################################################
# Taking things out for a spin, debugging.

# gains = [transfer_function(f_c, g, frequencies) for f_c, g in WHITE_PARAMS]

# Testing each set of parameters.
# gains = [gain_function(f_c, g, frequencies) for f_c, g in WHITE_PARAMS]
# gains = [gain_function(f_c, g, frequencies) for f_c, g in PINK_PARAMS]
# gains = [gain_function(f_c, g, frequencies) for f_c, g in RED_PARAMS]
#pprint(gains)
# sum_gains = [10*math.log(sum(gs)**2/1.0, 10) for gs in zip(*gains)]
# plt.semilogx(frequencies, sum_gains, basex=2)

# plt.grid(True)
# plt.ylim([-30, 30])
# plt.show()

################################################################################
# What if we just tried (log) interpolating between them?

# N = 10
# for i in range(N):
#     params = [10**( (math.log(rg, 10) - math.log(wg, 10)) * float(i)/(N-1) + math.log(wg, 10) )
#               for wg,rg in zip([g for _,g in WHITE_PARAMS], [g for _,g in RED_PARAMS])]

#     gains = [gain_function(f_c, g, frequencies)
#              for f_c, g in zip([f for f,_ in WHITE_PARAMS], params)]

#     sum_gains = [10*math.log(sum(gs)**2/1.0, 10) for gs in zip(*gains)]

#     plt.semilogx(frequencies, sum_gains, color=(float(N - i)/N, 0, float(i)/N))

################################################################################
# What if we tried interpolating between everything?

# N = 5
# for i in range(N):
#     params = [10**( (math.log(rg, 10) - math.log(wg, 10)) * float(i)/(N-1) + math.log(wg, 10) )
#               for wg,rg in zip([g for _,g in WHITE_PARAMS], [g for _,g in PINK_PARAMS])]

#     gains = [gain_function(f_c, g, frequencies)
#              for f_c, g in zip([f for f,_ in WHITE_PARAMS], params)]

#     sum_gains = [10*math.log(sum(gs)**2/1.0, 10) for gs in zip(*gains)]

#     plt.semilogx(frequencies, sum_gains, color=(float(N - i)/N, 0, float(i)/N))
# for i in range(N):
#     params = [10**( (math.log(rg, 10) - math.log(wg, 10)) * float(i)/(N-1) + math.log(wg, 10) )
#               for wg,rg in zip([g for _,g in PINK_PARAMS], [g for _,g in RED_PARAMS])]

#     gains = [gain_function(f_c, g, frequencies)
#              for f_c, g in zip([f for f,_ in WHITE_PARAMS], params)]

#     sum_gains = [10*math.log(sum(gs)**2/1.0, 10) for gs in zip(*gains)]

#     plt.semilogx(frequencies, sum_gains, color=(0, float(i)/N, float(N-i)/N))

################################################################################

# WHITE_PARAMS = [
#     (2000000,  1.0),
#     (16.5,   0.1),
#     (270.0,  0.1),
#     (5300.0, 0.1),
# ]
# SCALE = 0.2
# PINK_PARAMS = [
#     (2000000,  0.1848 * SCALE),
#     (16.5,     42.0 * SCALE),
#     (270.0,    8.0 * SCALE),
#     (5300.0,   2.5 * SCALE),
# ]

# def plot_total_and_parts(param_list, frequencies, color):
#     total_gains = None
#     for f_c, g in param_list:
#         gains = gain_function(f_c, g, frequencies)
#         db_gains = [10*math.log(g**2, 10) for g in gains]
#         plt.semilogx(frequencies, db_gains, color=[(4*1.0 + c)/5 for c in color])
#         if total_gains is None:
#             total_gains = gains
#         else:
#             total_gains = [sum(gs) for gs in zip(total_gains, gains)]
#     decible_gains = [10*math.log(g**2, 10) for g in total_gains]
#     plt.semilogx(frequencies, decible_gains, color=color)

# plot_total_and_parts(WHITE_PARAMS, frequencies, color=(1.0, 0, 0))

# plt.grid(True)
# plt.ylim([-30, 10])
# plt.show()

################################################################################
# What if we just tried (log) interpolating between them?

WHITE_PARAMS = [
    (2000000,  1.0),
    (16.5,   0.1),
    (270.0,  0.1),
    (5300.0, 0.1),
]
SCALE = 0.1
PINK_PARAMS = [
    (2000000,  0.1848 * SCALE),
    (16.5,     42.0 * SCALE),
    (270.0,    8.0 * SCALE),
    (5300.0,   2.5 * SCALE),
]
RED_PARAMS = [
    (2000000,  0.001),
    (16.5,   7.0),
    (270.0,  0.001),
    (5300.0, 0.001),
]

N = 5
for i in range(N):
    params = [10**( (math.log(rg, 10) - math.log(wg, 10)) * (1 - float(i)/(N-1))**2 + math.log(wg, 10) )
              for wg,rg in zip([g for _,g in WHITE_PARAMS], [g for _,g in PINK_PARAMS])]

    gains = [gain_function(f_c, g, frequencies)
             for f_c, g in zip([f for f,_ in WHITE_PARAMS], params)]

    sum_gains = [10*math.log(sum(gs)**2/1.0, 10) for gs in zip(*gains)]

    plt.semilogx(frequencies, sum_gains, color=(float(N - i)/N, 0, float(i)/N), basex=2)
for i in range(N):
    params = [10**( (math.log(rg, 10) - math.log(wg, 10)) * (float(i)/(N-1))**2 + math.log(wg, 10) )
              for wg,rg in zip([g for _,g in PINK_PARAMS], [g for _,g in RED_PARAMS])]

    gains = [gain_function(f_c, g, frequencies)
             for f_c, g in zip([f for f,_ in WHITE_PARAMS], params)]

    sum_gains = [10*math.log(sum(gs)**2/1.0, 10) for gs in zip(*gains)]

    plt.semilogx(frequencies, sum_gains, color=(0, float(i)/N, float(N-i)/N))

plt.grid(True)
plt.ylim([-30, 10])
plt.show()
