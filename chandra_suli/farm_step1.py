#!/usr/bin/env python

"""
Download files by observation ID, filter the event file, and separate by CCDs
"""

import argparse
import sys
import os

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.work_within_directory import work_within_directory


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Run following steps: download files by obsid, filter the event file, '
                                                 'and separate by CCD')

    parser.add_argument("-w", "--workdir", help="Directory for all the output (output files will be in a directory "
                                                "named after the obsid)", type=str, required=True)

    parser.add_argument("-o","--obsid",help="Observation ID Numbers", type=int, required=True)

    parser.add_argument('-r', '--region_repo', help="Path to the repository of region files",
                        type=str, required=True)

    parser.add_argument('-a',"--adj_factor",
                        help="If region files need to be adjusted, what factor to increase axes of ellipses by",
                        type=float, required=True)

    parser.add_argument("-e1","--emin",help="Minimum energy (eV)",type=int,required=True)

    parser.add_argument("-e2","--emax",help="Maximum energy (eV)",type=int,required=True)

    args = parser.parse_args()

    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    # Sanitize the workdir
    workdir = os.path.abspath(os.path.expandvars(os.path.expanduser(args.workdir)))

    with work_within_directory(workdir):

        # Download files

        cmd_line = "download_by_obsid.py --obsid %d" %args.obsid

        runner.run(cmd_line)

        try:

            evtfile = os.path.basename(find_files.find_files(os.getcwd(),'*%s*evt3.fits' %args.obsid)[0])
            tsvfile = os.path.basename(find_files.find_files(os.getcwd(),"%s.tsv" %args.obsid)[0])
            expmap = os.path.basename(find_files.find_files(os.getcwd(),"*%s*exp3.fits*" %args.obsid)[0])

        except IndexError:

            raise RuntimeError("\n\n\nCould not find one of the downloaded files for obsid %s. Exiting..." % args.obsid)

        # Create directory named after obsid
        if not os.path.exists(str(args.obsid)):

            os.mkdir(str(args.obsid))

        # Move files in there

        os.rename(evtfile, os.path.join(str(args.obsid), evtfile))
        os.rename(tsvfile, os.path.join(str(args.obsid), tsvfile))
        os.rename(expmap, os.path.join(str(args.obsid), expmap))

        # filtered_evtfile = "%d_filtered.fits" %(args.obsid)

        # # Filter regions
        #
        # # Figure out the path for the regions files for this obsid
        #
        # region_dir = os.path.join(os.path.expandvars(os.path.expanduser(args.region_repo)), '%s' % args.obsid)
        #
        # cmd_line = "filter_event_file.py --evtfile %s --tsvfile %s --region_dir %s --outfile %s --emin %d --emax %d " \
        #            "--adj_factor %s"\
        #            %(evtfile, tsvfile, region_dir, filtered_evtfile, args.emin, args.emax, args.adj_factor)
        #
        # runner.run(cmd_line)
        #
        # # Separate CCDs
        #
        # cmd_line = "separate_CCD.py --evtfile %s" %filtered_evtfile
        #
        # runner.run(cmd_line)