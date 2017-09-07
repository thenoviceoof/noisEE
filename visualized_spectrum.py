import math
import matplotlib
import matplotlib.pyplot as plt

# Draw the figures used in the blog.

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
# Example low pass filter.

gains = [gain_function(5000, 1.0, frequencies)]

plt.semilogx(frequencies, sum_gains_power(gains))
axes = plt.gca()
axes.set_xlabel('Log Frequency (Hz)')
axes.set_ylabel('Aural Power (dB)')

plt.grid(True)
plt.ylim([-15, 5])
plt.show()

################################################################################
# Three examples cutoffs

# Lines
plt.semilogx([400, 400], [0, -3], color='blue', dashes=[4, 5])
plt.semilogx([2000, 2000], [0, -3], color='green', dashes=[4, 5])
plt.semilogx([8000, 8000], [0, -3], color='red', dashes=[4, 5])

plt.semilogx(frequencies, sum_gains_power([gain_function(400, 1.0, frequencies)]),
             label='400 Hz Cutoff')
plt.semilogx(frequencies, sum_gains_power([gain_function(2000, 1.0, frequencies)]),
             label='2kHz Cutoff')
plt.semilogx(frequencies, sum_gains_power([gain_function(8000, 1.0, frequencies)]),
             label='8kHz Cutoff')
axes = plt.gca()
axes.set_xlabel('Log Frequency (Hz)')
axes.set_ylabel('Aural Power (dB)')

plt.grid(True)
plt.legend()
plt.ylim([-20, 5])
plt.show()

################################################################################
# Linear segments + 3db tangent

gains = gain_function(2000, 1.0, frequencies)
power_gains = sum_gains_power([gains])
plt.semilogx(frequencies, power_gains)

# Plot the start/end asymptotes.
plt.semilogx([10, 40000], [0.0, 0.0], color='green')
# Starting at 20kHz, go backwards 2 decades to 200Hz, and then go
# forwards an octave to 400Hz
y_start = power_gains[-1] + 20 * 2 - 20 * math.log(2, 10)
# Starting at 20kHz, go forwards an octave to 40kHz
y_end =   power_gains[-1] - 20 * math.log(2, 10)
plt.semilogx([400, 40000], [y_start, y_end], color='green')

# Plot the -3db tangent.
tangent_x = 2000
tangent_y = -20 * math.log(2, 10)/2
tangent_x_start = 200
tangent_y_start = tangent_y + 10 # +3db/octave == +10db/decade
tangent_x_end = 40000
tangent_y_end = tangent_y - 10 - 10 * math.log(2, 10)
plt.semilogx([tangent_x_start, tangent_x_end], [tangent_y_start, tangent_y_end],
             color='red', label='-3db/octave tangent')

axes = plt.gca()
axes.set_xlabel('Log Frequency (Hz)')
axes.set_ylabel('Aural Power (dB)')

plt.grid(True)
plt.legend()
plt.ylim([-25, 5])
plt.show()

################################################################################
# 3x pinking filter

PINK_3x_SCALE =  0.05
f1 = gain_function(2000000,  0.1848 * PINK_3x_SCALE, frequencies)
f2 = gain_function(16.5,     42.0 * PINK_3x_SCALE, frequencies)
f3 = gain_function(270.0,    8.0 * PINK_3x_SCALE, frequencies)
f4 = gain_function(5300.0,   2.5 * PINK_3x_SCALE, frequencies)

plt.semilogx(frequencies, sum_gains_power([f1, f2, f3, f4]))
plt.semilogx(frequencies, sum_gains_power([f1]), color='grey')
plt.semilogx(frequencies, sum_gains_power([f2]), color='grey')
plt.semilogx(frequencies, sum_gains_power([f3]), color='grey')
plt.semilogx(frequencies, sum_gains_power([f4]), color='grey')
axes = plt.gca()
axes.set_xlabel('Log Frequency (Hz)')
axes.set_ylabel('Aural Power (dB)')

plt.grid(True)
plt.ylim([-50, 10])
plt.show()
