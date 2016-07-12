#!/usr/bin/env python

"""
Run all steps of pipeline with one command
"""

import argparse
import sys
import os

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Download event files and exposure map from the Chandra catalog')

    parser.add_argument("-o","--obsid",help="Observation ID Numbers", type=int, required=True)

    parser.add_argument('-r', '--region_repo', help="Path to the repository of region files",
                        type=str, required=True)

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

    parser.add_argument("-e1","--emin",help="Minimum energy (eV)",type=int,required=True)

    parser.add_argument("-e2","--emax",help="Maximum energy (eV)",type=int,required=True)

    args = parser.parse_args()

    # Get the logger

    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    # Download files

    cmd_line = "download_by_obsid.py --obsid %d" %args.obsid

    runner.run(cmd_line)

    evtfile = os.path.basename(find_files.find_files(os.getcwd(),'*evt3.fits')[0])
    tsvfile = os.path.basename(find_files.find_files(os.getcwd(),"%d.tsv" %args.obsid)[0])
    expfile = os.path.basename(find_files.find_files(os.getcwd(),"*exp3.fits.gz")[0])

    filtered_evtfile = "%d_filtered.fits" %(args.obsid)

    # Filter regions

    # Figure out the path for the regions files for this obsid

    region_dir = os.path.join(os.path.expandvars(os.path.expanduser(args.region_repo)), '%s' % args.obsid)

    cmd_line = "filter_event_file.py --evtfile %s --region_dir %s --outfile %s --emin %d --emax %d" %(evtfile,
                                                                                                      region_dir,
                                                                                                      filtered_evtfile,
                                                                                                      args.emin,
                                                                                                      args.emax)

    runner.run(cmd_line)

    # Separate CCDs

    cmd_line = "separate_CCD.py --evtfile %s" %filtered_evtfile

    runner.run(cmd_line)

    ccd_files = find_files.find_files('.','ccd*fits')

    # Run Bayesian Blocks algorithm

    for ccd_file in ccd_files:

        cmd_line = "xtdac.py -e %s -x %s -w no -c %s -p %s -s %s" \
                   %(ccd_file, expfile, args.ncpus, args.typeIerror, args.sigmaThreshold)

        runner.run(cmd_line)


    ccd_bb_files = find_files.find_files('.','ccd*txt')

    # Check for closest variable source

    for ccd_bb_file in ccd_bb_files:

        og_file = os.path.basename(ccd_bb_file)

        check_var_file = "check_var_%s" %og_file

        cmd_line = "check_variable.py --bbfile %s --tsvfile %s --outfile %s" %(ccd_bb_file,tsvfile,check_var_file)

        runner.run(cmd_line)

