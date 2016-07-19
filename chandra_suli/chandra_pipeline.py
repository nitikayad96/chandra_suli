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

    parser.add_argument('-a',"--adj_factor",
                        help="If region files need to be adjusted, what factor to increase axes of ellipses by",
                        type=float, required=True)

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

    parser.add_argument("-w", "--writeRegionFiles",
                        help="Write a ds9 region file for each region with excesses?",
                        type=str,
                        default='yes',
                        required=False,
                        choices=['yes', 'no'])

    parser.add_argument("-v", "--verbosity", help="Info or debug", type=str, required=False, default='info',
                        choices=['info', 'debug'])

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

    evtfile = os.path.basename(find_files.find_files(os.getcwd(),'*%s*evt3.fits' %args.obsid)[0])
    tsvfile = os.path.basename(find_files.find_files(os.getcwd(),"%s.tsv" %args.obsid)[0])
    expfile = os.path.basename(find_files.find_files(os.getcwd(),"*%s*exp3.fits.gz" %args.obsid)[0])

    filtered_evtfile = "%d_filtered.fits" %(args.obsid)

    # Filter regions

    # Figure out the path for the regions files for this obsid

    region_dir = os.path.join(os.path.expandvars(os.path.expanduser(args.region_repo)), '%s' % args.obsid)

    cmd_line = "filter_event_file.py --evtfile %s --tsvfile %s --region_dir %s --outfile %s --emin %d --emax %d " \
               "--adj_factor %s"\
               %(evtfile, tsvfile, region_dir, filtered_evtfile, args.emin, args.emax, args.adj_factor)

    runner.run(cmd_line)

    # Separate CCDs

    cmd_line = "separate_CCD.py --evtfile %s" %filtered_evtfile

    runner.run(cmd_line)

    ccd_files = find_files.find_files('.','ccd*%s*fits'%args.obsid)

    # Run Bayesian Blocks algorithm
    ccd_bb_files = []

    for ccd_file in ccd_files:

        cmd_line = "xtdac.py -e %s -x %s -w %s -c %s -p %s -s %s -v %s" \
                   %(ccd_file, expfile, args.writeRegionFiles, args.ncpus, args.typeIerror,
                     args.sigmaThreshold, args.verbosity)

        runner.run(cmd_line)

        # xtdac uses as output file the name of the input file, without the extension,
        # plus "_res.txt"

        root_name = os.path.splitext(ccd_file)[0]

        output_file = '%s_res.txt' %root_name

        if os.path.exists(output_file):

            ccd_bb_files.append(output_file)

        else:

            raise RuntimeError("xtdac.py failed and didn't produce any output file (looking for %s)" % output_file)


    # Check for hot pixels
    # Check for closest variable source across any observation

    for i in xrange(len(ccd_bb_files)):

        og_file = os.path.basename(ccd_bb_files[i])

        ccd_bb_file = ccd_bb_files[i]
        ccd_file = ccd_files[i]

        check_hp_file = "check_hp_%s" %og_file

        cmd_line = "check_hot_pixel.py --evtfile %s --bbfile %s --outfile %s" \
                   %(ccd_file, ccd_bb_file, check_hp_file)

        runner.run(cmd_line)

        check_var_file = "check_var_%s" %og_file

        cmd_line = "check_variable_revised.py --bbfile %s --outfile %s --eventfile %s" \
                   %(check_hp_file,check_var_file, evtfile)

        runner.run(cmd_line)

