

"""
Take evt3 file and use region files to subtract off sources that are already known - image will have lots of holes
Goals by Friday 6/31 - Get script working for one image at a time

below = code used by Giacomo to create filtered image
ftcopy 'acisf00635_000N001_evt3.fits[EVENTS][regfilter("my_source.reg")]' test.fits
"""