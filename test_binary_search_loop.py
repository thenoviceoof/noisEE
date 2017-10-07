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

# Make sure that the chosen filter values will always exit the loop
# with reasonable values.

filter0016x = [0, 5734, 11693, 16030, 19274, 21684, 29121, 32767]
filter0016y = [0, 1478, 6579, 13111, 22962, 26764, 29850, 32767]

filter0270x = [0, 3400, 9726, 16331, 19395, 22078, 25416, 32767]
filter0270y = [1612, 6132, 22206, 32767, 13003, 4342, 807, 0]

filter5300x = [0, 2219, 7419, 10704, 16275, 20965, 24791, 32767]
filter5300y = [5264, 10757, 28662, 32767, 29869, 8733, 1838, 0]

filter0000x = [0, 3468, 9517, 11880, 15385, 25149, 28630, 32767]
filter0000y = [32767, 32249, 10444, 5091, 1519, 363, 180, 80]

filters = [
    (filter0016x, filter0016y),
    (filter0270x, filter0270y),
    (filter5300x, filter5300y),
    (filter0000x, filter0000y),
]

for i in range(len(filters)):
    xs, ys = filters[i]
    print i
    for j in range(1024):
        if j % 32 == 0:
            print '  ' + str(j)
            x = j << 5

        # Binary search through the xs array to find the two values
        # we should be interpolating between.
        # The current index represents the range that we expect the
        # value to be within.
        minIndex = 0
        maxIndex = 6 # The max index is 7, but it's just an endpoint.
        while minIndex != maxIndex:
            midIndex = (minIndex + maxIndex)/2
            if x < xs[midIndex]:
                maxIndex = midIndex - 1
            elif x > xs[midIndex + 1]:
                minIndex = midIndex + 1
            else: # x >= xs[midIndex] && x <= xs[midIndex + 1]
                maxIndex = midIndex
                break
        assert xs[maxIndex] <= x and x <= xs[maxIndex + 1]
