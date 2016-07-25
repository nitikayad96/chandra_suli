#!/usr/bin/env python

"""
Check each candidate for hot pixels and nearest variable sources
"""

import argparse
import os
import sys

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.work_within_directory import work_within_directory

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Check each candidate transient for hot pixels and '
                                                 'closest variable source')

    parser.add_argument("-o","--obsid",help="Observation ID Numbers", type=int, required=True, nargs = "+")

    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    args = parser.parse_args()

    for this_obsid in args.obsid:

        if not os.path.exists(str(this_obsid)):

            raise IOError("Directory not found for obsid %s" %this_obsid)

        with work_within_directory(str(this_obsid)):

            ccd_files = find_files.find_files('.','ccd*%s*fits'%this_obsid)
            ccd_files = sorted(ccd_files)

            ccd_bb_files = find_files.find_files('.', 'ccd*%s*res.txt' %this_obsid)
            ccd_bb_files = sorted(ccd_bb_files)

            evtfile = find_files.find_files('.','*%s*evt3.fits' %this_obsid)[0]


            for i in xrange(len(ccd_bb_files)):

                og_file = os.path.basename(ccd_bb_files[i])

                ccd_bb_file = ccd_bb_files[i]
                ccd_file = ccd_files[i]

                check_hp_file = "check_hp_%s" %og_file

                cmd_line = "check_hot_pixel_revised.py --evtfile %s --bbfile %s --outfile %s --debug no" \
                           %(ccd_file, ccd_bb_file, check_hp_file)

                runner.run(cmd_line)

                check_var_file = "check_var_%s" %og_file

                cmd_line = "check_variable_revised.py --bbfile %s --outfile %s --eventfile %s" \
                           %(check_hp_file,check_var_file, evtfile)

                runner.run(cmd_line)