#!/usr/bin/env python

"""
Generate lightcurves for each candidate given a list of candidates
"""

import argparse
import os
import sys
import numpy as np

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.sanitize_filename import sanitize_filename

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Generate light curves for transients listed in a'
                                                 'master list')

    parser.add_argument("--masterfile", help="Path to file containing list of transients",
                        required=True, type=str)
    parser.add_argument("--data_path", help="Path to directory containing data of all obsids", required = True,
                        type=str)


    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    args = parser.parse_args()

    # Get data from masterfile



    masterfile = sanitize_filename(args.masterfile)

    transient_data = np.array(np.recfromtxt(masterfile, names=True), ndmin=1)

    for transient in transient_data:

        obsid = transient['Obsid']
        ccd = transient['CCD']
        candidate = transient['Candidate']
        tstart = transient['Tstart']
        tstop = transient['Tstop']

        # use region file from xtdac and cut region

        region = find_files.find_files(obsid, )





