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

    parser.add_argument('-r', '--region_repo', help="Path to the repository of region files",
                        type=str, required=True)

    parser.add_argument("-o","--obsid",help="Observation ID Numbers", type=int, required=True, nargs = '+')

    args = parser.parse_args()

    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    # Sanitize the workdir
    workdir = os.path.abspath(os.path.expandvars(os.path.expanduser(args.workdir)))
    regdir = os.path.abspath(os.path.expandvars(os.path.expanduser(args.region_repo)))

    with work_within_directory(workdir):

        # Download files

        for this_obsid in args.obsid:

            regdir_this_obsid = os.path.join(regdir,str(this_obsid))
            print regdir_this_obsid
            print os.path.exists(regdir_this_obsid)

            if os.path.exists(regdir_this_obsid):

                cmd_line = "download_by_obsid.py --obsid %d" %this_obsid

                runner.run(cmd_line)

                try:

                    evtfile = os.path.basename(find_files.find_files(os.getcwd(),'*%s*evt3.fits' %this_obsid)[0])
                    tsvfile = os.path.basename(find_files.find_files(os.getcwd(),"%s.tsv" %this_obsid)[0])
                    expmap = os.path.basename(find_files.find_files(os.getcwd(),"*%s*exp3.fits*" %this_obsid)[0])

                except IndexError:

                    raise RuntimeError("\n\n\nCould not find one of the downloaded files for obsid %s. Exiting..."
                                       % this_obsid)

                # Create directory named after obsid
                if not os.path.exists(str(this_obsid)):

                    os.mkdir(str(this_obsid))

                # Move files in there

                os.rename(evtfile, os.path.join(str(this_obsid), evtfile))
                os.rename(tsvfile, os.path.join(str(this_obsid), tsvfile))
                os.rename(expmap, os.path.join(str(this_obsid), expmap))

            else:

                print "Region files do not exist for ObsID %s" %this_obsid
