from collections import defaultdict
import math
import matplotlib.pyplot as plt
import numpy
import random

from pprint import pprint

# Constants
SAMPLING_FREQUENCY = 44100
SAMPLING_PERIOD = 1.0/SAMPLING_FREQUENCY

################################################################################
# Utility functions to generate data.

def even_log_frequencies(n=200, low_frequency=20, high_frequency=20000):
    high_log = math.log(high_frequency, 10)
    low_log = math.log(low_frequency, 10)
    logs = [(high_log - low_log)*(float(i)/n)+low_log for i in range(n)]
    return [10**l for l in logs]

FREQUENCIES = even_log_frequencies()
FREQUENCIES_LOG10 =  numpy.log10(FREQUENCIES)

def gain_function(f_c, gain, frequencies, sampling_period=SAMPLING_PERIOD):
    gains = [gain/(f/f_c + 1) for f in frequencies]
    return gains

################################################################################
# Starting parameters
WHITE_PARAMS = [
    (2000000,  1.0),
    (16.5,     0.1),
    (270.0,    0.1),
    (5300.0,   0.1),
]
PINK_SCALE = 0.15
PINK_PARAMS = [
    (2000000,  0.1848 * PINK_SCALE),
    (16.5,     42.0 * PINK_SCALE),
    (270.0,    8.0 * PINK_SCALE),
    (5300.0,   2.5 * PINK_SCALE),
]
RED_PARAMS = [
    (2000000, 0.001),
    (16.5,    8.0),
    (270.0,   0.001),
    (5300.0,  0.001),
]

################################################################################
# Fit and iterate.

def loss_function(m, b, target_m, target_b, error):
    m_error = abs(target_m - m)

    # Use the intercept at 20Hz
    fake_b = b + m * math.log10(20)
    b_error = abs(target_b - fake_b)
    return 0.1 * error + 5 * m_error + b_error

def get_loss_from_data(decibels, target_m, target_b):
    xs = FREQUENCIES_LOG10
    ys = decibels
    fit, error, _, _, _ = numpy.polyfit(xs, ys, 1, full=True)

    m, b = fit
    return loss_function(m, b, target_m, target_b, error[0]**0.5)

def get_loss_from_parameters(parameters, target_m, target_b):
    gains = [gain_function(f_c, g, FREQUENCIES) for f_c,g in parameters]
    decibel_gains = [10*math.log10(sum(gs)**2) for gs in zip(*gains)]
    return get_loss_from_data(decibel_gains, target_m, target_b)

def explore(parameters, target_m, target_b):
    min_loss =  get_loss_from_parameters(parameters, target_m, target_b)
    step_size = 1 - 1./(min_loss + 1)
    min_parameters =  parameters
    changes = 0
    for i in range(20000):
        g_step = step_size * 2 * (random.random() - 0.5)
        local_parameters = [(f_c, 10**(math.log10(g) + g_step))
                            for f_c,g in min_parameters]
        loss = get_loss_from_parameters(local_parameters, target_m, target_b)
        if loss < min_loss:
            min_loss = loss
            min_parameters = local_parameters
            step_size = 1 - 1./(min_loss/10. + 1)
            changes += 1
    print 'Changed {} times'.format(changes)
    return min_loss, min_parameters

def interval_explore(start_parameters, stop_parameters, m_interval, b_interval, n=11):
    all_parameters = []
    gain_parameters = list(zip([g for _,g in start_parameters],
                               [g for _,g in stop_parameters]))
    for i in range(n):
        fraction = float(i)/(n-1)
        # Targets
        m = m_interval[0] * (1 - fraction) + m_interval[1] * fraction
        b = b_interval[0] * (1 - fraction) + b_interval[1] * fraction
        # Interpolated input
        interpolated_parameters = [10**( math.log10(lower) * (1 - fraction) +
                                         math.log10(upper) * fraction)
                                   for lower, upper in gain_parameters]
        combined_parameters = [(s[0], g) for s,g in zip(start_parameters,
                                                        interpolated_parameters)]

        loss, parameters = explore(combined_parameters, m, b)
        all_parameters.append( ((m, b), parameters) )
        print m, b, loss
    return all_parameters

################################################################################
# Main

N = 31

white_pink_parameters = interval_explore(PINK_PARAMS, WHITE_PARAMS, (-10, 0), (10, 0), n = N)
pink_red_parameters = interval_explore(PINK_PARAMS, RED_PARAMS, (-10, -20), (10, 20), n = N)

# for i,ps in enumerate(white_pink_parameters):
#     lines, parameters = ps
#     gains = [gain_function(f_c, g, FREQUENCIES) for f_c,g in parameters]
#     decibel_gains = [10*math.log10(sum(gs)**2) for gs in zip(*gains)]
#     plt.semilogx(FREQUENCIES, decibel_gains, color=(0, float(i)/N, float(N-i)/N))
# for i,ps in enumerate(pink_red_parameters):
#     lines, parameters = ps
#     gains = [gain_function(f_c, g, FREQUENCIES) for f_c,g in parameters]
#     decibel_gains = [10*math.log10(sum(gs)**2) for gs in zip(*gains)]
#     plt.semilogx(FREQUENCIES, decibel_gains, color=(0, float(i)/N, float(N-i)/N))

# plt.grid(True)
# plt.ylim([-40, 20])
# plt.show()

################################################################################

freq_map = defaultdict(list)
for line_params,gen_params in white_pink_parameters:
    m = line_params[0]
    for freq, gain in gen_params:
        freq_map[freq].append((m, gain))
for line_params,gen_params in pink_red_parameters:
    m = line_params[0]
    for freq, gain in gen_params:
        freq_map[freq].append((m, gain))
for i, entry in enumerate(freq_map.iteritems()):
    freq, values = entry
    sorted_values =  sorted(values, key=lambda x: x[0])
    m_values = [m for m,_ in sorted_values]
    g_values = [g for _,g in sorted_values]
    # g_values = [10*math.log10(g**2) for _,g in sorted_values]
    plt.plot(m_values, g_values,
             color=(0, float(len(freq_map)-i)/len(freq_map), float(i)/len(freq_map)),
             label=str(freq))
    plt.legend()

plt.grid(True)
plt.show()

# Write it out to a CSV
m_map = defaultdict(dict)
for freq, values in freq_map.iteritems():
    for m, g in values:
        m_map[m]['slope'] = str(m)
        m_map[m][str(freq)] = str(g)

csv_file = open('gains.csv', 'w')
columns = ['slope'] + sorted(str(k) for k in freq_map.keys())
csv_file.write(','.join(columns) +  '\n')
for m,inner_dict in m_map.iteritems():
    csv_file.write(','.join([inner_dict[c] for c in columns]) + '\n')
csv_file.close()
