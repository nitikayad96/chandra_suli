#!/usr/bin/env python

"""
Run CIAO tool vtpdetect to find sources in areas listed as potential transients
"""

import argparse
import os
import sys
import astropy.io.fits as pyfits
from astropy.coordinates import SkyCoord
import numpy as np

from chandra_suli.unique_list import unique_list
from chandra_suli.sanitize_filename import sanitize_filename
from chandra_suli import find_files
from chandra_suli.run_command import CommandRunner
from chandra_suli import logging_system

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run vtpdetect to find sources in regions given by xtdac")

    parser.add_argument("--masterfile", help="Path to file containing list of transients in this set",
                        required=True, type=str)
    parser.add_argument("--outfile", help="Name of output file which will contain modified list of transients")
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
    outfile = os.path.join(outdir, sanitize_filename(args.outfile))

    # Get data from master list
    master_data = np.array(np.recfromtxt(masterfile, names=True), ndmin=1)
    vtpdetect_data = []

    for i in range(len(master_data)):

        obsid = master_data['Obsid'][i]
        ra = master_data['RA'][i]
        dec = master_data['Dec'][i]
        ccd = master_data['CCD'][i]
        candidate = master_data['Candidate'][i]
        tstart = master_data['Tstart'][i]
        tstop = master_data['Tstop'][i]
        obsid_dir = os.path.join(data_dir,str(obsid))

        all_regions_file = find_files.find_files(obsid_dir, '%s_all_regions.fits' %(obsid))[0]
        evtfile = find_files.find_files(obsid_dir, 'ccd_%s_%s_filtered.fits' %(ccd,obsid))[0]
        expfile = find_files.find_files(obsid_dir, '*%s*exp3*' %obsid)[0]

        expfile_new = os.path.join(outdir, "%s_cheesemask.fits" % obsid)

        if not os.path.exists(expfile_new):

            with pyfits.open(evtfile, memmap=False) as f:

                if len(f) < 4:

                    cmd_line = "fappend %s[1] %s" %(all_regions_file, evtfile)
                    runner.run(cmd_line)


            # run this to create filtered exposure map to match filtered event file to use during vtpdetect

            cmd_line = "xtcheesemask.py -i %s -r %s -o %s -s 1 --no-reverse" \
                       %(expfile, evtfile, expfile_new)

            runner.run(cmd_line)

        # create new event file with just time interval found by xtdac

        evtfile_new = os.path.join(outdir, 'ccd_%s_%s_filtered_TI_%s.fits' %(ccd,obsid,candidate))

        cmd_line = 'ftcopy \"%s[(TIME >= %s) && (TIME <= %s)]\" %s clobber=yes ' \
                   % (evtfile, tstart, tstop, evtfile_new)

        runner.run(cmd_line)

        # run vtpdetect

        vtpdetect_file = os.path.join(outdir,'ccd_%s_%s_filtered_candidate_%s_vtpdetect.fits' %(ccd,obsid,candidate))

        cmd_line = 'vtpdetect %s expfile=%s outfile=%s ellsigma=1 limit=1e-5 coarse=3 maxiter=10 scale=1 clobber=yes' \
                   %(evtfile_new, expfile_new, vtpdetect_file)

        runner.run(cmd_line)

        # Check contents of file

        with pyfits.open(vtpdetect_file,memmap=False) as h:

            regions = h['SRCLIST'].data

            # further analysis if not empty

            if len(regions) != 0:

                # check that the source in question is related to that given by xtdac by checking to see if it's
                # within a circle having a radius of the major axis of the region

                for j in xrange(len(regions)):

                    radius = max(regions['R'][j])


                    ra_reg = regions['RA'][j]
                    dec_reg = regions['DEC'][j]

                    p1 = SkyCoord(ra,dec, unit = "deg")
                    p2 = SkyCoord(ra_reg, dec_reg, unit = "deg")

                    sep = p2.separation(p1).arcsec

                    temp_list = []

                    if sep <= 2 * radius:

                        fsp = regions['FSP'][j]

                        temp_list.extend(master_data[i])
                        temp_list.append(float(fsp))

                        vtpdetect_data.append(temp_list)

            else:

                os.remove(vtpdetect_file)
                os.remove(evtfile_new)

    with open(args.outfile, "w") as k:

        existing_column_names = " ".join(master_data.dtype.names)

        k.write("# %s Significance\n" % existing_column_names)

        vtpdetect_data_unique = unique_list(vtpdetect_data, range(1, len(master_data.dtype.names)))

        for n,i in enumerate(range(len(vtpdetect_data_unique))):

            temp_list = []

            temp_list.append(str(n+1))

            for j in range(1,len(master_data.dtype.names)+1):

                temp_list.append(str(vtpdetect_data_unique[i][j]))

            line = " ".join(temp_list)

            k.write("%s\n" % line)








