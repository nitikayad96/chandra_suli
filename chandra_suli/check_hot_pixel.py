#!/usr/bin/env python

"""
Check each candidate transient from Bayesian Block algorithm to see if it is actually a hot pixel
"""

import subprocess
import argparse
import os
import sys
import numpy as np
import astropy.io.fits as pyfits

from chandra_suli.run_command import CommandRunner
from chandra_suli import logging_system



if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Check to see if transient candidates are actually hot pixels")

    parser.add_argument("--evtfile",help="Filtered CCD file",required=True)
    parser.add_argument("--bbfile",help="Text file for one CCD with transient candidates listed",required=True)
    parser.add_argument("--outfile",help="Name of output file",required=True)

    # Get logger for this command

    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Instance the command runner

    runner = CommandRunner(logger)

    args = parser.parse_args()

    evtfile = os.path.abspath(os.path.expandvars(os.path.expanduser(args.evtfile)))
    bbfile = os.path.abspath(os.path.expandvars(os.path.expanduser(args.bbfile)))

    # read BB data into array
    bb_data = np.array(np.recfromtxt(bbfile,names=True), ndmin=1)

    # number of rows of data
    bb_n = len(bb_data)

    with open(args.outfile, "w") as f:

        # Pre-existing column names
        existing_column_names = " ".join(bb_data.dtype.names)

        f.write("# %s Hot_Pixel_Flag\n" % existing_column_names)

        for i in xrange(bb_n):

            ra = bb_data['RA'][i]
            dec = bb_data['Dec'][i]
            tstart = bb_data['Tstart'][i]
            tstop = bb_data['Tstop'][i]

            # isolate region of event within times given
            temp_file_hp = "__check_hotpix.fits"
            cmd_line = "dmcopy \"%s[sky=circle(%sd,%sd,15'') && time=%s:%s]\" %s" \
                       %(args.evtfile, ra, dec, tstart, tstop, temp_file_hp)

            runner.run(cmd_line)

            hotpix_flag = False

            # If all events happening in same coordinate, flag as hot pixel
            with pyfits.open(temp_file_hp, memmap=False) as hotpix:

                chipx = hotpix['EVENTS'].data.chipx
                chipy = hotpix['EVENTS'].data.chipy

                if len(np.unique(chipx)) == 1 and len(np.unique(chipy)) == 1:

                    hotpix_flag = True


            temp_list = []

            for j in xrange(len(bb_data.dtype.names)):

                temp_list.append(str(bb_data[i][j]))

            # Fill "Hot_Pixel_Flag" column

            temp_list.append(str(hotpix_flag))

            line = " ".join(temp_list)

            f.write("%s\n" % line)

            os.remove(temp_file_hp)











