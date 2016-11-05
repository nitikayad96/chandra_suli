#!/usr/bin/env python

"""
Run CIAO's celldetect tool
"""

import argparse
import os
import sys

import astropy.io.fits as pyfits
import numpy as np

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli import work_within_directory
from chandra_suli.run_command import CommandRunner
from chandra_suli.sanitize_filename import sanitize_filename

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Check to see if transient candidates are actually hot pixels")

    parser.add_argument("--masterfile", help="Path to file containing list of transients in this set",
                        required=True, type=str)
    parser.add_argument("--outfile", help="Name of output file which will contain modified list of transients")
    parser.add_argument("--ranks", help="Ranks in file that you want to run", nargs="+", required=False, default=[0],
                        type=int)
    parser.add_argument("--data_dir", help="Path to directory containing data of all obsids", required=True,
                        type=str)
    parser.add_argument("--outdir", help="Directory where output files will go", required=True, type=str)

    # Get logger for this command

    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Instance the command runner

    runner = CommandRunner(logger)

    args = parser.parse_args()

    masterfile = sanitize_filename(args.masterfile)
    data_dir = sanitize_filename(args.data_dir)
    outdir = sanitize_filename(args.outdir)

    # Get data from master list
    master_data = np.array(np.recfromtxt(masterfile, names=True), ndmin=1)
    celldetect_data = []

    if args.ranks[0] == 0:

        ranks = range(1, len(master_data) + 1)

    else:

        ranks = args.ranks

    for rank in ranks:

        # index of object in question will be one less than the rank (first source is index 0, etc)
        idx = rank - 1

        obsid = master_data['Obsid'][idx]
        ccd = master_data['CCD'][idx]
        candidate = master_data['Candidate'][idx]
        tstart = master_data['Tstart'][idx]
        tstop = master_data['Tstop'][idx]
        obsid_dir = os.path.join(data_dir, str(obsid))

        evtfile = find_files.find_files(obsid_dir, 'ccd_%s_%s_filtered.fits' % (ccd, obsid))[0]
        regfile = find_files.find_files(obsid_dir, 'ccd_%s_%s_filtered_candidate_%s.reg' % (ccd, obsid, candidate))[0]

        regfile_name = os.path.splitext(os.path.basename(regfile))[0]
        newreg = "%s_reg.fits" % regfile_name
        newreg_path = os.path.join(outdir, newreg)

        cmd_line = 'ftcopy \"%s[regfilter(\'%s\') && (TIME >= %s) && (TIME <= %s)]\" %s clobber=yes ' \
                   % (evtfile, regfile, tstart, tstop, newreg_path)

        runner.run(cmd_line)

        celldetect_file = '%s_celldetect.fits' % regfile_name
        celldetect_path = os.path.join(outdir, celldetect_file)

        cmd_line = 'celldetect %s %s clobber=yes' % (newreg_path, celldetect_path)
        runner.run(cmd_line)

        with pyfits.open(celldetect_path, memmap=False) as f:

            regions = f['SRCLIST'].data

        if len(regions) != 0:

            celldetect_data.append(master_data[idx])

        else:

            os.remove(celldetect_path)
            os.remove(newreg_path)

    with work_within_directory.work_within_directory(outdir):

        with open(args.outfile, "w") as f:

            existing_column_names = " ".join(master_data.dtype.names)

            f.write("# %s\n" % existing_column_names)

            for n, i in enumerate(range(len(celldetect_data))):

                temp_list = []

                temp_list.append(str(n + 1))

                for j in range(1, len(master_data.dtype.names)):
                    temp_list.append(str(celldetect_data[i][j]))

                line = " ".join(temp_list)

                f.write("%s\n" % line)
