#!/usr/bin/env python

"""
Transfer files to correct location before running farm_step3 script
"""

import argparse
import os
import sys

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.sanitize_filename import sanitize_filename
from chandra_suli.work_within_directory import work_within_directory

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Check each candidate transient for hot pixels and '
                                                 'closest variable source')

    parser.add_argument("-o", "--obsid", help="Observation ID Numbers", type=int, required=True, nargs="+")
    parser.add_argument("-f", "--outfile", help="Name of output file which will contain filtered list of transients",
                        required=True)
    parser.add_argument("-d1", "--results_path", help="Path to directory containing results from farm_step_2")
    parser.add_argument("-d2", "--data_path", help="Path to directory containing data of all obsids", required=True,
                        type=str)

    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    args = parser.parse_args()

    results_path = sanitize_filename(args.results_path)
    data_path = sanitize_filename(args.data_path)

    for this_obsid in args.obsid:

        # Go to directory where results from farm_step2 are stored

        with work_within_directory(results_path):

            # Find files related to just this_obsid

            this_obsid_files = find_files.find_files(".", "*_%s_*" % this_obsid)
            this_obsid_files.extend(find_files.find_files(".", "%s_*" % this_obsid))

            # move each file to the corresponding data folder

        for file_path in this_obsid_files:
            new_path = os.path.join(data_path, str(this_obsid), os.path.basename(file_path))

            os.rename(file_path, new_path)

        cmd_line = "farm_step3.py --obsid %s --outfile %s --data_path %s" \
                   % (this_obsid, args.outfile, args.data_path)

        runner.run(cmd_line)
