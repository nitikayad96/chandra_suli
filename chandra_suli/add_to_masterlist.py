#!/usr/bin/env python

"""
Take each CCD file, already checked for hot pixels and cross matched for variable sources, and add remaining candidate
transients to master list
"""

import os
import argparse
import sys
import numpy as np

from chandra_suli.run_command import CommandRunner
from chandra_suli import logging_system



if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Add filtered candidates to a masterlist of sources")

    parser.add_argument("--bbfile",help="Input text file (already checked for hot pixels and variable sources",
                        required=True, type=str)
    parser.add_argument("--masterfile",help="Name of file containing master list of all potential transients",
                        required=True, type=str)


    # Get logger for this command

    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Instance the command runner

    runner = CommandRunner(logger)

    args = parser.parse_args()

    # get directory path and file name from input file arguments

    bb_file_path = os.path.abspath(os.path.expandvars(os.path.expanduser(args.bbfile)))

    # read BB data into array
    bb_data = np.array(np.recfromtxt(bb_file_path,names=True), ndmin=1)

    # number of rows of data
    bb_n = len(bb_data)


    # If fresh list is to be started

    if not os.path.exists(args.masterfile):

        existing_column_names = " ".join(bb_data.dtype.names)

        # new array with relevant data
        master_data = []

        with open(args.masterfile,"w") as f:

            f.write("# Rank %s Checked\n" % existing_column_names)

            # Only consider candidates that aren't marked as hot pixels

            for i in range(bb_n):

                if bb_data['Hot_Pixel_Flag'][i] == False:

                    master_data.append(bb_data[i])

            # sort according to PSF fraction, highest to lowest

            master_data_sorted = sorted(master_data, key=lambda data_row: data_row[-1], reverse=True)

            # Write all sources to text file

            for i in range(len(master_data_sorted)):

                temp_list = []

                temp_list.append(str(i+1))

                for j in xrange(len(bb_data.dtype.names)):

                    temp_list.append(str(master_data_sorted[i][j]))

                # Mark all sources as unchecked initially. When you go through and run wavdetect, manually change to yes
                temp_list.append("no")

                line = " ".join(temp_list)

                f.write("%s\n" % line)


    else:

        # Get original data from master list
        master_data_og = np.array(np.recfromtxt(args.masterfile, names=True), ndmin=1)

        # Transform it to a python list from a numpy array
        master_data_new = master_data_og.tolist()

        existing_column_names = " ".join(master_data_og.dtype.names)

        with open(args.masterfile,"w") as f:

            f.write("# %s\n" % existing_column_names)

            for i in range(bb_n):

                temp_list = []

                # Add candidate to master list if it's not a hot pixel
                if bb_data['Hot_Pixel_Flag'][i] == False:

                    temp_list = [0]
                    temp_list.extend(bb_data[i])
                    temp_list.append("no")

                    master_data_new.append(temp_list)

            # Sort new master list according to decreasing PSF fraction order

            master_data_sorted = sorted(master_data_new, key=lambda data_row: data_row[-2], reverse=True)

            # Write to file
            for i in range(len(master_data_sorted)):

                temp_list = []
                temp_list.append(str(i+1))

                for j in xrange(1,len(master_data_og.dtype.names)):

                    temp_list.append(str(master_data_sorted[i][j]))

                line = " ".join(temp_list)

                f.write("%s\n" % line)


















