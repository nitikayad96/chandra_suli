#!/usr/bin/env python

"""
Run xtdac for each CCD file
"""

import argparse
import os
import sys

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Run Bayesian Block algorithm')

    parser.add_argument("-o","--obsid",help="Observation ID Numbers", type=int, required=True)

    parser.add_argument("-c", "--ncpus", help="Number of CPUs to use (default=1)",
                        type=int, default=1, required=False)

    parser.add_argument("-p", "--typeIerror",
                        help="Type I error probability for the Bayesian Blocks algorithm.",
                        type=float,
                        default=1e-5,
                        required=False)

    parser.add_argument("-s", "--sigmaThreshold",
                        help="Threshold for the final significance. All intervals found "
                             "by the bayesian blocks "
                             "algorithm which does not surpass this threshold will not be saved in the "
                             "final file.",
                        type=float,
                        default=5.0,
                        required=False)

    parser.add_argument("-m", "--multiplicity", help="Control the overlap of the regions."
                                                     " A multiplicity of 2 means the centers of the regions are"
                                                     " shifted by 1/2 of the region size (they overlap by 50 percent),"
                                                     " a multiplicity of 4 means they are shifted by 1/4 of "
                                                     " their size (they overlap by 75 percent), and so on.",
                        required=False, default=2.0, type=float)

    parser.add_argument("-v", "--verbosity", help="Info or debug", type=str, required=False, default='info',
                        choices=['info', 'debug'])


    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    args = parser.parse_args()

    # Find filtered ccd files to input to xtdac
    ccd_files = find_files.find_files('.','ccd*%s*fits'%args.obsid)

    expfile = os.path.basename(find_files.find_files(os.getcwd(), "*%s*exp3.fits.gz" % args.obsid)[0])

    # Run Bayesian Blocks algorithm

    for ccd_file in ccd_files:

        cmd_line = "xtdac.py -e %s -x %s -w yes -c %s -p %s -s %s -m %s -v %s" \
                   %(ccd_file, expfile, args.ncpus, args.typeIerror,
                     args.sigmaThreshold, args.multiplicity, args.verbosity)

        runner.run(cmd_line)

