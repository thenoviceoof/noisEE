#!/usr/bin/env python
################################################################################
# Script to find families of digital filter parameters that produce arbitrary
# falloff, in pursuit of noise of any color.
################################################################################

import argparse
import array
from numpy import fft
import wave

def read_wav(path):
    wav_file = wave.open(path)

    assert wav_file.getnchannels() == 1
    assert wav_file.getframerate() == 44100, 'Expect 44.1k audio'
    assert wav_file.getnframes() <= 44100, 'Expect less than a second of audio'
    assert wav_file.getsampwidth() == 2, 'Expected signed 16 bit audio'

    data_string = wav_file.readframes(wav_file.getnframes())

    # Convert the data from string to byte(s) array
    data = array.array('h')
    data.fromstring(data_string)

    return list(data)

def main(wav_path):
    data = read_wav(wav_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('wavpath', help='')

    args = parser.parse_args()

    main(args.wavpath)
