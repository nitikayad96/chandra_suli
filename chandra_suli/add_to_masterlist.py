#!/usr/bin/env python

"""
Take each CCD file, already checked for hot pixels and cross matched for variable sources, and add remaining candidate
transients to master list
"""

import os
import argparse
import sys
import numpy as np
import pandas as pd

from chandra_suli.run_command import CommandRunner
from chandra_suli import logging_system


if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Add filtered candidates to a masterlist of sources")

    parser.add_argument("--bbfile",help="Input text file (already checked for hot pixels and variable sources",
                        required=True, type=str)
    parser.add_argument("--masterfile",help="Path to file containing list of transients in this set",
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

    # column names
    existing_column_names = " ".join(bb_data.dtype.names)


    # If fresh list is to be started

    if not os.path.exists(args.masterfile):

        # new array with relevant data
        master_data = np.empty(shape=[0, len(bb_data[0])])

    else:

        master_data = np.array(np.recfromtxt(args.masterfile, names=True), ndmin=1)

    # Append new data to existing data

    for i in range(bb_n):

        np.concatenate(master_data, bb_data[i])

    data_all = pd.DataFrame.from_records(master_data)

    # Drop all duplicates

    data_unique = data_all.drop_duplicates(subset=['Candidate','Obsid','CCD'])

    # Keep only data satisfying the following conditions

    idx = (data_unique['PSFfrac'] > 0.95) & (data_unique['Probability'] < 1e-5) \
                & (data_unique['Hot_Pixel_Flag']==False)

    # Sort according to PSFfrac

    master_data_sorted = sorted(data_unique[idx], key=lambda data_row: data_row[-1], reverse=True)

    # Write data to text file

    with open(args.masterfile,"w") as f:

        f.write("# Rank %s\n" % existing_column_names)

        i = 0

        while i < len(master_data_sorted):

            temp_list = []

            temp_list.append(str(i+1))

            for j in xrange(len(bb_data.dtype.names)):

                temp_list.append(str(master_data_sorted[i][j]))

            line = " ".join(temp_list)

            f.write("%s\n" % line)

            i += 1
















