#!/usr/bin/env python
################################################################################
# Create the fixed-point int array representation of the piece-wise
# linear approximations.

import array
import csv
import math

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
# Output the parameters.

def fixed_point_parameters(params):
    index_dict = {
        'constant': 0,
        'low': 1,
        'medium': 2,
        'high': 3,
    }

    for name, linear_fn in params.iteritems():
        max_gain = max([g for _,g in linear_fn])
        max_value = (2**15)-1
        x_array = []
        y_array = []

        # Do it from the low X to high X (low slope to high slope).
        for i in reversed(range(len(linear_fn))):
            # x: (-20, 0) => (2**16-1, 0)
            x_value = int(round((linear_fn[i][0]/-20.0)*max_value))
            assert x_value >= 0 and x_value <= max_value
            x_array.append(str(x_value))
            # y: (0, max_gain) => (0, 2**16-1)
            y_value = int(round((linear_fn[i][1]/max_gain)*max_value))
            assert y_value >= 0 and x_value <= max_value
            y_array.append(str(y_value))

        print name
        print ', '.join(x_array)
        print ', '.join(y_array)

fixed_point_parameters(params)
