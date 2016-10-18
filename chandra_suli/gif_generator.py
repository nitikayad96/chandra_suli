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
from matplotlib.animation import ArtistAnimation

from chandra_suli.find_files import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.sanitize_filename import sanitize_filename

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Generate gifs to visualize transient')

    parser.add_argument("--masterfile", help="Path to file containing list of transients",
                        required=True, type=str)
    parser.add_argument("--data_path", help="Path to directory containing data of all obsids", required=True,
                        type=str)

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

        event_file = find_files(os.path.join(data_path, str(obsid)), "ccd_%s_%s_filtered.fits" % (ccd, obsid))[0]

        intervals = [tstart, tstop]

        # get start and stop time of observation
        with pyfits.open(event_file, memmap=False) as reg:
            tmin = reg['EVENTS'].header['TSTART']
            tmax = reg['EVENTS'].header['TSTOP']

        print "Duration: %s" %duration
        print "Tmax: %s" %tmax
        print "Tmin: %s" %tmin
        print "Obs Time: %s" %(tmax-tmin)

        # Ensure that there will only be a maximum of 5 frames
        while len(intervals) < 7:

            # this loop creates a list of time intervals with which to create gif from

            if tmin < (intervals[0] - duration) or tmax > (intervals[-1] + duration):

                if tmin < intervals[0] - duration:

                    intervals.insert(0,intervals[0] - duration)

                if tmax > intervals[-1] + duration:

                        intervals.append(intervals[-1] + duration)

            else:

                break


        print intervals


        evt_names = os.path.splitext(event_file)

        # Create individual time interval files
        for i in range(len(intervals)-1):

            outfile = os.path.join(data_path, str(obsid), "%s_TI_%s_cand_%s%s" %(evt_names[0], i+1, candidate, evt_names[1]))

            cmd_line = 'ftcopy \"%s[(TIME >= %s) && (TIME <= %s)]\" %s clobber=yes ' \
                       % (event_file, intervals[i], intervals[i+1], outfile)

            runner.run(cmd_line)

        #sort all time interval fits files
        images = find_files('.', "%s_TI*cand_%s%s" %(evt_names[0], candidate, evt_names[1]))
        img_sort = sorted(images)

        #create a list of frames that will be animated into a gif
        frames = []

        for image in img_sort:

            #get x and y coordinates of image from fits file
            data = pyfits.getdata(image)
            x = data.field("x")
            y = data.field("y")

            #create 2D histogram data from it
            sbs.set(rc={'axes.facecolor': 'black', 'axes.grid': False})
            img = plt.hist2d(x, y, bins=60, norm=LogNorm())

            #get binned coordinates
            X = img[1]
            Y = img[2]

            #smooth data
            gauss_kernel = Gaussian2DKernel(0.75)
            smoothed_data_gauss = convolve(img[0], gauss_kernel)

            #format it for hot colors
            plt.hot()
            plt.colorbar()

            fig, axes = plt.subplots(nrows=1, ncols=1)

            img2 = axes.matshow(smoothed_data_gauss.T, origin='lower')

            axes.set_title("ObsID %s, CCD %s \nTstart = %s, Tstop = %s" %(obsid, ccd, tstart, tstop))
            axes.set_yticklabels([])
            axes.set_xticklabels([])

            #add this image to list of frames
            frames.append([img2])

        #create new figure to animate gif
        fig2 = plt.figure()

        #animate and save gif
        print "Creating gif ObsID %s, CCD %s, Candidate %s...\n" %(obsid, ccd, candidate)
        anim = ArtistAnimation(fig2, frames, interval=200)
        anim.save("%s_cand_%s.gif" %(evt_names[0], candidate))

        plt.close()


