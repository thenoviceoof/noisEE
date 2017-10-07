noiseEE
================================================================================
Code to find a set of easily derivable software filters to produce
different flavors of noise and intermediate stages, and a hardware
realization.

If you want a full explanation of the project, see notes [part
1](http://thenoviceoof.com/blog/projects/noisee-part-1-software/) and
[part
2](http://thenoviceoof.com/blog/projects/noisee-part-2-hardware/).

filter/
--------------------------------------------------------------------------------
Contains scripts to help find and visualize the filter parameters.

- `exploration_parameters.py`: exploratory work, lots of commented out
  code. Generates graphics to investigate whether simple parameter
  interpolation would work.

- `ideal_parameters.py`: hill climb the gain parameters of a 3 low
  pass filter joint filter to create linear slope approximations,
  using ideal filter transfer functions. Generates `gains.csv`.

- `linear_approximation.R`: takes in `gains.csv` (currently a more
  specific name; you'll need to edit the file) and uses R's segmented
  library to get a piecewise linear approximation. Generates
  `linear_parameters.csv`.

- `generate_hardware_parameter.py`: takes in `linear_parameters.csv`,
  and prints out 16-bit fixed-point integer gain parameters for use in
  `noisEE.c`.

There are also scripts generating multimedia:

- `generate_audio.py`: given the piecemeal results in
  `linear_parameters.csv`, generate a WAV file sweeping from white to
  red noise.

- `visualized_spectrum.py`: running this will generate figures used in
  [part 1 of the project
  notes](http://thenoviceoof.com/blog/projects/noisee-part-1-software/).

- `visualized_animated_spectrum.py`: running this will generate
  animation frames used for the spectrum animation in [part 1 of the
  project
  notes](http://thenoviceoof.com/blog/projects/noisee-part-1-software/).

hardware/
--------------------------------------------------------------------------------
Contains the hardware design files.

- `noisEE-project*`: KiCad design files. Start with the `.pro` project file.

- `noisEE-components*`: contains the OPA227 symbol and MEE1SC footprint
  for KiCad.

- `case__1_5mm.svg/case__3_0mm.svg`: the SVG design files fit into
  Ponoko's P1 template, meant for their respective wood thicknesses.

- `case_*.svg`: these SVGs are intermediate design files, mostly
  correcting for laser kerf.

avr/
--------------------------------------------------------------------------------
Contains files for programming the AVR.

- `Makefile`: just run `make` to build and upload, if you have `avr-gcc`
  and `avrdude` on your path, and are using the ISP MKII. You'll need
  to edit this file if you're using something else.

- `noisEE.c`: currently in a bad state, checkpointed in the middle of
  testing how each filter affects the final response. If you want to
  continue work, you'll need to remove the test loop and uncomment the
  real runtime loop.

(other)
--------------------------------------------------------------------------------

- test_binary_search_loop.py: a quick script to make sure that a
  binary search on the calculated filter values will terminate.
