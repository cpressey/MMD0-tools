MMD0-tools
==========

This is a set of Python scripts and modules for working with files in MMD0
(Amiga MED module) format.

Right now they are in a very crude state.  The ultimate goal is to have
something that converts most of the data in them to Csound format, where
they can be cleaned up (consistent panning per instrument, and so forth.)

Currently, the `mmd0.py` script can dump most of the contents of an MMD0
file in a nominally human-readable format, and can extract the samples used
as the instruments.

As I'm doing this primarily for my own MED tunes, I don't plan to support
the features of MED that I never personally used, such as synthesized
instruments.
