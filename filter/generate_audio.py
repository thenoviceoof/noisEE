#!/usr/bin/env python
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

# Generate audio from changing gain parameters.

import array
import csv
import math
import wave

from pprint import pprint

SAMPLE_RATE = 44100.0

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
# Generate noise.

def read_wav(path):
    wav_file = wave.open(path)

    assert wav_file.getnchannels() == 1, 'Expect monochannel audio'
    assert wav_file.getframerate() == SAMPLE_RATE, 'Expect 44.1k audio'
    assert wav_file.getsampwidth() == 2, 'Expected signed 16 bit audio'

    data_string = wav_file.readframes(wav_file.getnframes())

    # Convert the data from string to byte(s) array
    data = array.array('h')
    data.fromstring(data_string)

    return list(data)

data = read_wav('white_noise.wav')

################################################################################
# Filter the noise.

def slope_to_coefficients(params, slope):
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
        fc_gain[index_dict[name]][1] = gain

    # Convert the fc/gain params to a function
    tmp_coefs = [(1-(1/SAMPLE_RATE)/(1/(2*math.pi*fc) + 1/SAMPLE_RATE), gain)
                for fc, gain in fc_gain]
    coefs = [(A, gain*(1-A)) for A, gain in tmp_coefs]
    return coefs

def apply_continuous_filter(params, slope_spec, data):
    # Prep coefficients
    fc_gain = [[2000000, None], [16.5, None], [270.0, None], [5300.0, None]]
    index_dict = {
        'constant': 0,
        'low': 1,
        'medium': 2,
        'high': 3,
    }
    max_slope, min_slope = slope_spec

    # Apply to the data.
    output_data = []
    filtered = [0, 0, 0, 0]
    for i,d in enumerate(data):
        slope = float(max_slope - min_slope)*(float(i)/len(data)) + min_slope
        coefs = slope_to_coefficients(params, slope)
        filtered = [cf[0] * prev + cf[1] * d for prev,cf in zip(filtered, coefs)]
        raw_output = sum(filtered)
        trim_output = min(max(int(raw_output), -2**15), 2**15 - 1)
        output_data.append(trim_output)
    return output_data

output_data = apply_continuous_filter(params, [-20, 0], data)

################################################################################
# Write the noise to a WAV.

def write_wav(data):
    wav_file = wave.open('filtered_noise.wav', 'w')
    wav_file.setnchannels(1)
    wav_file.setframerate(SAMPLE_RATE)
    wav_file.setsampwidth(2)

    # Convert from byte(s) array to string
    arr = array.array('h')
    arr.fromlist(data)
    wav_file.writeframes(arr.tostring())

write_wav(output_data)
