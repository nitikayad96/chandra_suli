#!/usr/bin/env python

"""
Run all steps of pipeline with one command
"""

import argparse
import subprocess
import os

from chandra_suli import find_files

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Download event files and exposure map from the Chandra catalog')

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

    parser.add_argument("-e1","--emin",help="Minimum energy (eV)",type=int,required=True)

    parser.add_argument("-e2","--emax",help="Maximum energy (eV)",type=int,required=True)

    args = parser.parse_args()

    # Download files

    cmd_line = "download_by_obsid.py --obsid %d" %args.obsid

    subprocess.check_call(cmd_line,shell=True)

    evtfile = os.path.basename(find_files.find_files(os.getcwd(),'*evt2.fits.gz')[0])
    tsvfile = os.path.basename(find_files.find_files(os.getcwd(),"%d.tsv" %args.obsid)[0])
    expfile = os.path.basename(find_files.find_files(os.getcwd(),"*exp3.fits.gz")[0])
    filtered_evtfile = "%d_filtered.fits" %(args.obsid)

    # Filter regions

    cmd_line = "filter_by_regions.py --evtfile %s --outfile %s --emin %d --emax %d" %(evtfile, filtered_evtfile, args.emin, args.emax)

    subprocess.check_call(cmd_line,shell=True)

    # Separate CCDs

    cmd_line = "separate_CCD.py --evtfile %s" %filtered_evtfile

    subprocess.check_call(cmd_line,shell=True)

    ccd_files = find_files.find_files('.','ccd*fits')

    # Run Bayesian Blocks algorithm

    for ccd_file in ccd_files:

        cmd_line = "xtdac.py -e %s -x %s -w no -c %d -p %d -s %d" \
                   %(ccd_file, expfile, args.cpu, args.typeIerror, args.sigmaThreshold)
        subprocess.check_call(cmd_line,shell=True)


    ccd_bb_files = find_files.find_files('.','ccd*txt')

    # Check for closest variable source

    for ccd_bb_file in ccd_bb_files:

        og_file = os.path.basename(ccd_bb_file)

        check_var_file = "check_var_%s" %og_file

        cmd_line = "check_variable.py --bbfile %s --tsvfile %s --outfile %s" %(ccd_bb_file,tsvfile,check_var_file)

        subprocess.check_call(cmd_line,shell=True)

