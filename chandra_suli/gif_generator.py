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

from chandra_suli import find_files
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

        event_file = find_files.find_files(os.path.join(data_path, str(obsid)), "ccd_%s_%s_filtered.fits" % (ccd, obsid))[0]

        intervals = [tstart, tstop]

        # get start and stop time of observation
        with pyfits.open(event_file, memmap=False) as reg:
            tmin = reg['EVENTS'].header['TSTART']
            tmax = reg['EVENTS'].header['TSTOP']

        # Ensure that there will only be a maximum of 5 frames
        if len(intervals) <= 7:

            # this loop creates a list of time intervals with which to create gif from

            if tmin < intervals[0] - duration:

                intervals[0] = intervals[0] - duration

            if tmax > intervals[-1] + duration:

                    intervals[-1] = intervals[-1] + duration


        evt_names = os.path.splitext(event_file)

        # Create individual time interval files
        for i in range(len(intervals)-1):

            outfile = os.path.join(data_path, str(obsid), "%s_TI_%s_cand_%s%s" %(evt_names[0], i+1, candidate, evt_names[1]))

            cmd_line = 'ftcopy \"%s[(TIME >= %s) && (TIME <= %s)]\" %s clobber=yes ' \
                       % (event_file, intervals[i], intervals[i+1], outfile)

            runner.run(cmd_line)


