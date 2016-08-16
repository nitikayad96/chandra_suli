#!/usr/bin/env python

"""
Generate lightcurves for each candidate given a list of candidates
"""

import argparse
import os
import sys
import numpy as np
import astropy.io.fits as pyfits
import matplotlib.pyplot as plt
import seaborn as sbs

from chandra_suli import find_files
from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.sanitize_filename import sanitize_filename

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Generate light curves for transients listed in a'
                                                 'master list')

    parser.add_argument("--masterfile", help="Path to file containing list of transients",
                        required=True, type=str)
    parser.add_argument("--data_path", help="Path to directory containing data of all obsids", required = True,
                        type=str)


    # Get the logger
    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Get the command runner
    runner = CommandRunner(logger)

    args = parser.parse_args()

    # Get data from masterfile

    data_path = sanitize_filename(args.data_path)
    masterfile = sanitize_filename(args.masterfile)

    transient_data = np.array(np.recfromtxt(masterfile, names=True), ndmin=1)

    for transient in transient_data:

        obsid = transient['Obsid']
        ccd = transient['CCD']
        candidate = transient['Candidate']
        tstart = transient['Tstart']
        tstop = transient['Tstop']

        # use region file from xtdac and cut region

        regions = find_files.find_files(str(obsid), "ccd_%s_%s_filtered_candidate_%s.reg" %(ccd, obsid, candidate))
        event_file = find_files.find_files(str(obsid), "ccd_%s_%s_filtered.fits" %(ccd, obsid))[0]

        if len(regions) != 1:

            raise IOError("More than one region file found")

        else:

            region = regions[0]

        evt_reg = "ccd_%s_%s_filtered_candidate_%s_reg.fits" %(ccd, obsid, candidate)

        cmd_line = "ftcopy \'%s[EVENTS][regfilter(\"%s\")]\' %s clobber=yes " %(event_file, region, evt_reg)

        runner.run(cmd_line)

        data = pyfits.getdata(evt_reg)

        sbs.set(font_scale=2)
        sbs.set_style('white')

        fig = plt.figure(figsize=(15, 15 / 1.33333))

        duration = tstop - tstart

        bins = np.arange(-10 * duration, 10 * duration, duration)

        time = data.field("TIME")

        rate, obins, _ = plt.hist(time - tstart, bins, weights=np.ones(time.shape[0]) * 1.0 / duration,
                                  color='white')

        # Centers of the bins

        tc = (bins[:-1] + bins[1:]) / 2.0

        plt.errorbar(tc, rate, yerr=np.sqrt(rate * duration) / duration, fmt='.')

        plt.axvline(0, linestyle=':')
        plt.axvline(duration, linestyle=':')

        plt.xlabel("Time since trigger (s)")
        plt.ylabel("Count rate (cts/s)")
        plt.title("Transient Lightcurve\nObsID = %s, CCD ID = %s, Candidate=%s\n" %(obsid, ccd, candidate))

        plot_file = "ccd_%s_%s_candidate_%s_lightcurve.png" %(ccd, obsid, candidate)

        plt.savefig(plot_file)

        os.rename(plot_file, os.path.join(data_path, str(obsid), plot_file))
        os.rename(evt_reg,os.path.join(data_path, str(obsid), evt_reg))



