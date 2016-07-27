#!/usr/bin/env python

"""
Run CIAO's celldetect tool
"""

import argparse
import os
import sys
import numpy as np


from chandra_suli import find_files
from chandra_suli.run_command import CommandRunner
from chandra_suli import logging_system

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Check to see if transient candidates are actually hot pixels")

    parser.add_argument("--masterfile",help="Name of file containing master list of all potential transients",
                        required=True, type=str)
    parser.add_argument("--ranks",help="Ranks in file that you want to run",nargs="+",required=True,type=int)
    parser.add_argument("--data_dir", help="Path to directory containing data of all obsids", required=True,
                        type=str)
    parser.add_argument("--outdir",help="Directory where output files will go",required=True, type=str)

    # Get logger for this command

    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Instance the command runner

    runner = CommandRunner(logger)

    args = parser.parse_args()

    # Get data from master list
    master_data = np.array(np.recfromtxt(args.masterfile, names=True), ndmin=1)

    for rank in args.ranks:

        # index of object in question will be one less than the rank (first source is index 0, etc)
        idx = rank - 1

        obsid = master_data['Obsid'][idx]
        ccd = master_data['CCD'][idx]
        candidate = master_data['Candidate'][idx]
        tstart = master_data['Tstart'][idx]
        tstop = master_data['Tstop'][idx]
        obsid_dir = os.path.join(args.data_dir,str(obsid))

        evtfile = find_files.find_files(obsid_dir, 'ccd_%s_%s_filtered.fits' %(ccd,obsid))[0]
        regfile = find_files.find_files(obsid_dir, 'ccd_%s_%s_filtered_candidate_%s.reg' %(ccd,obsid,candidate))[0]

        regfile_name = os.path.splitext(os.path.basename(regfile))[0]
        outfile = "%s_celldetect.fits" %regfile_name
        outfile_path = os.path.join(args.outdir,outfile)

        cmd_line = 'ftcopy \"%s[regfilter(\'%s\') && (TIME >= %s) && (TIME <= %s)]\" %s clobber=yes '\
                   %(evtfile, regfile, tstart, tstop, outfile_path)

        runner.run(cmd_line)


