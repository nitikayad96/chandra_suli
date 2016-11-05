#!/usr/bin/env python

"""
Generate lightcurves for each candidate given a list of candidates
"""

import argparse
import os
import sys
import numpy as np
import astropy.io.fits as pyfits
import matplotlib.pyplot as plt
import seaborn as sbs
from matplotlib.colors import LogNorm
from astropy.convolution import convolve, Gaussian2DKernel
from matplotlib.animation import ArtistAnimation, FFMpegWriter

from chandra_suli.find_files import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.sanitize_filename import sanitize_filename

import matplotlib
matplotlib.use("tkagg")

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Generate gifs to visualize transient')

    parser.add_argument("--masterfile", help="Path to file containing list of transients",
                        required=True, type=str)
    parser.add_argument("--data_path", help="Path to directory containing data of all obsids", required=True,
                        type=str)

    parser.add_argument("--verbose-debug", action='store_true')

    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    args = parser.parse_args()

    data_path = sanitize_filename(args.data_path)
    masterfile = sanitize_filename(args.masterfile)

    transient_data = np.array(np.recfromtxt(masterfile, names=True), ndmin=1)

    for transient in transient_data:

        obsid = transient['Obsid']
        ccd = transient['CCD']
        candidate = transient['Candidate']
        tstart = transient['Tstart']
        tstop = transient['Tstop']

        duration = tstop-tstart

        event_file = find_files(os.path.join(data_path, str(obsid)), "ccd_%s_%s_filtered_nohot.fits" % (ccd, obsid))[0]

        # get start and stop time of observation
        with pyfits.open(event_file, memmap=False) as event_ext:

            tmin = event_ext['EVENTS'].header['TSTART']
            tmax = event_ext['EVENTS'].header['TSTOP']

            # Get minimum and maximum X and Y, so we use always the same binning for the images
            xmin, xmax = event_ext['EVENTS'].data.field("X").min(), event_ext['EVENTS'].data.field("X").max()
            ymin, ymax = event_ext['EVENTS'].data.field("Y").min(), event_ext['EVENTS'].data.field("Y").max()

        print "Duration: %s" %duration
        print "Tmin: %s" % tmin
        print "Tmax: %s" %tmax
        print "Obs Time: %s" %(tmax-tmin)

        # Use the interval before the transient and the interval after the transient, as well as of course
        # the interval of the transient itself

        intervals = [tmin]

        # Add tstart only if it is sufficiently different from tmin (so we don't get an empty interval when the
        # transient is right at the beginning)

        if abs(tstart - tmin) > 0.1:

            intervals.append(tstart)

        intervals.append(tstop)

        # Add tmax only if it is sufficiently different from tstop, so we don't get an empty interval when the
        # transient is right at the end)

        if abs(tmax - tstop) > 0.1:

            intervals.append(tmax)

        evt_name, evt_file_ext = os.path.splitext(os.path.basename(event_file))

        # Create individual time interval files
        images = []

        for i in range(len(intervals)-1):

            outfile = "%s_TI_%s_cand_%s%s" %(evt_name, i+1, candidate, evt_file_ext)

            cmd_line = 'ftcopy \"%s[(TIME >= %s) && (TIME <= %s)]\" %s clobber=yes ' \
                       % (event_file, intervals[i], intervals[i+1], outfile)

            runner.run(cmd_line)

            images.append(outfile)

        #create a list of frames that will be animated into a gif
        frames = []

        # Prepare bins
        xbins = np.linspace(xmin, xmax, 300)
        ybins = np.linspace(ymin, ymax, 300)

        fig = plt.figure()

        sub = fig.add_subplot(111)
        sub.set_title("ObsID %s, CCD %s \nTstart = %s, Tstop = %s" % (obsid, ccd, tstart, tstop))

        for i, image in enumerate(images):

            #get x and y coordinates of image from fits file
            data = pyfits.getdata(image)
            x = data.field("x")
            y = data.field("y")

            #create 2D histogram data from it
            sbs.set(rc={'axes.facecolor': 'black', 'axes.grid': False})

            hh, X, Y = np.histogram2d(x, y, bins=[xbins, ybins])

            #smooth data
            gauss_kernel = Gaussian2DKernel(stddev=0.7, x_size=9, y_size=9)
            smoothed_data_gauss = convolve(hh, gauss_kernel, normalize_kernel=True)

            if x.shape[0] > 0:

                img = sub.imshow(smoothed_data_gauss, cmap='hot', animated=True, origin='lower')

            else:

                # No events in this image. Generate an empty image
                img = sub.imshow(smoothed_data_gauss, cmap='hot', animated=True, origin='lower')

            text = sub.annotate("%i / %i" % (i+1, len(images)), xy=(xbins.shape[0]/2.0, -20),
                                xycoords='data', annotation_clip=False)

            # Compute interval duration
            dt = intervals[i+1] - intervals[i]

            text2 = sub.annotate("%i events" % (x.shape[0]), xy=(-120, ybins.shape[0]/2.0),
                                xycoords='data', annotation_clip=False)

            text3 = sub.annotate("Duration: %.2f s" % (dt), xy=(-120, ybins.shape[0]/2.0 + 30),
                                 xycoords='data', annotation_clip=False)

            sub.set_yticklabels([])
            sub.set_xticklabels([])

            #add this image to list of frames
            frames.append([img, text, text2, text3])

            # Remove the image
            os.remove(image)

        #animate and save gif
        print "Creating gif ObsID %s, CCD %s, Candidate %s...\n" %(obsid, ccd, candidate)
        anim = ArtistAnimation(fig, frames, interval=2000)
        anim.save("%s_cand_%s.gif" %(evt_name, candidate), writer='imagemagick')

        plt.close()


