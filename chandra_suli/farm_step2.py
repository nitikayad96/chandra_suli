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
from chandra_suli.work_within_directory import work_within_directory

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Run Bayesian Block algorithm')

    parser.add_argument("-o","--obsid",help="Observation ID Numbers", type=int, required=True)

    parser.add_argument('-r', '--region_repo', help="Path to the repository of region files",
                        type=str, required=True)

    parser.add_argument('-a', "--adj_factor",
                        help="If region files need to be adjusted, what factor to increase axes of ellipses by",
                        type=float, required=True)

    parser.add_argument("-e1", "--emin", help="Minimum energy (eV)", type=int, required=True)

    parser.add_argument("-e2", "--emax", help="Maximum energy (eV)", type=int, required=True)

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

    if not os.path.exists(str(args.obsid)):

        raise IOError("Directory not found for obsid %s" %args.obsid)

    with work_within_directory(str(args.obsid)):

        # Find filtered ccd files to input to xtdac
        ccd_files = find_files.find_files('.','ccd*%s*fits'%args.obsid)

        evtfile = find_files.find_files(os.getcwd(),'*%s*evt3.fits' %args.obsid)[0]
        tsvfile = find_files.find_files(os.getcwd(),"%s.tsv" %args.obsid)[0]
        expfile = find_files.find_files(os.getcwd(), "*%s*exp3.fits.gz" % args.obsid)[0]

        filtered_evtfile = "%d_filtered.fits" %(args.obsid)

        # Figure out the path for the regions files for this obsid

        region_dir = os.path.join(os.path.expandvars(os.path.expanduser(args.region_repo)), '%s' % args.obsid)

        cmd_line = "filter_event_file.py --evtfile %s --tsvfile %s --region_dir %s --outfile %s --emin %d --emax %d " \
                   "--adj_factor %s"\
                   %(evtfile, tsvfile, region_dir, filtered_evtfile, args.emin, args.emax, args.adj_factor)

        runner.run(cmd_line)

        # Separate CCDs

        cmd_line = "separate_CCD.py --evtfile %s" %filtered_evtfile

        runner.run(cmd_line)

        ccd_files = find_files.find_files('.', 'ccd*%s*fits' % args.obsid)

        # Run Bayesian Blocks algorithm

        for ccd_file in ccd_files:

            cmd_line = "xtdac.py -e %s -x %s -w yes -c %s -p %s -s %s -m %s -v %s" \
                       %(ccd_file, expfile, args.ncpus, args.typeIerror,
                         args.sigmaThreshold, args.multiplicity, args.verbosity)

            runner.run(cmd_line)

