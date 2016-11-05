#!/usr/bin/env python

"""
Pre-filter event file for obvious hot pixels (to gain execution time). A further, deeper search for hot pixel will be
executed after the Bayesian Block stage
"""

import argparse
import os
import sys

import astropy.io.fits as pyfits
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import euclidean_distances

from chandra_suli import logging_system
from chandra_suli.run_command import CommandRunner
from chandra_suli.sanitize_filename import sanitize_filename


def neighbor_pixel_check(cluster_coords, max_distance=2):
    """
    Check that all events in the cluster have a maximum distance smaller than max_distance

    :param cluster_coords:
    :param max_distance:
    :return:
    """

    hot_pix_flag = True

    all_distances = euclidean_distances(cluster_coords, cluster_coords)
    if args.debug == "yes":
        print all_distances

    for distances in all_distances:

        for distance in distances:

            if distance < max_distance:
                pass

            else:
                hot_pix_flag = False
                break

        if hot_pix_flag == False:
            break

    return hot_pix_flag


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Check to see if transient candidates are actually hot pixels")

    parser.add_argument("--evtfile", help="Filtered CCD file", required=True, type=str)
    parser.add_argument("--outfile", help="Output file with events in hot pixels removed", required=True, type=str)
    parser.add_argument("--debug", help="Debug mode? (yes or no)", required=False, default='no')

    # Get logger for this command

    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Instance the command runner

    runner = CommandRunner(logger)

    args = parser.parse_args()

    eventfile = sanitize_filename(args.evtfile)

    # Open event file

    fits_file = pyfits.open(eventfile, mode='update', memmap=False)

    # Make sure we are dealing with only one CCD
    ccds = np.unique(fits_file['EVENTS'].data.ccd_id)

    # Get frame time

    frame_time = fits_file['EVENTS'].header['TIMEDEL']

    # Get the data extension

    data = fits_file['EVENTS'].data

    for ccd in ccds:

        logger.info("Processing CCD %s" % ccd)

        # Select all events in this CCD
        ccd_idx = (data.ccd_id == ccd)

        # Find unique times (frame times)

        unique_time_stamps = np.unique(data[ccd_idx].time)

        # Loop over each frame time

        tot_hot_pixels = 0

        for i, time_stamp in enumerate(unique_time_stamps):

            # sys.stderr.write("\r %s out of %s" % (i+1, unique_time_stamps.shape[0]))

            # Find events within 3 time frames (0.1 is a tolerance to avoid rounding problems)

            tstart = time_stamp - 0.1
            tstop = time_stamp + 20.0 # 3 * frame_time + 0.1

            time_idx = np.where((data.time >= tstart) & (data.time <= tstop)
                                & (data.pha != -1)
                                & (data.ccd_id == ccd))[0]

            chipx = data.chipx[time_idx]
            chipy = data.chipy[time_idx]

            # Run the check only if there are events in these frame times

            if 2 < len(chipx) < 10:

                # Organize into list of coordinate pairs
                coords = np.vstack([chipx, chipy]).T

                # Run DBSCAN
                # Eps is the maximum distance between events for them to be considered in the same cluster

                db = DBSCAN(eps=2, min_samples=2).fit(coords)
                l = db.labels_
                csi = db.core_sample_indices_
                c = db.components_

                # Unique clusters

                labels_unique = np.unique(l)

                if len(labels_unique) == 1 and labels_unique[0] == -1:
                    # No clusters
                    continue

                # if len(labels_unique) > 1:

                #    import pdb;pdb.set_trace()

                for i, cluster in enumerate(labels_unique):

                    if cluster == -1:
                        # Unclustered events

                        continue

                    # Gather all events within this cluster
                    c_idx = np.where(l == cluster)[0]

                    if c_idx.shape[0] < 2:

                        # Only one element here, not a bright pixel
                        continue

                    if neighbor_pixel_check(coords[c_idx, :]):

                        n_events = c_idx.shape[0]

                        print("Found hot pixel at %s between %s and %s (%s events)" % (coords[0, :], tstart,
                                                                                       tstop, n_events))

                        tot_hot_pixels += 1

                        fits_file['EVENTS'].data.pha[c_idx] = -1

    # Count how many events we are filtering out
    n_filtered = np.sum(fits_file['EVENTS'].data.pha == -1)

    n_tot = int(fits_file['EVENTS'].data.shape[0])

    fits_file.close()

    print("\n")

    logger.info("Found %s non-unique hot pixels" % tot_hot_pixels)
    logger.info(
        "Filtering out %s events out of %s (%.2f percent)" % (n_filtered, n_tot, float(n_filtered) / n_tot * 100.0))

    outfile = sanitize_filename(args.outfile)

    cmd_line = "ftcopy %s[EVENTS][pha!=-1] %s  copyall=true clobber=yes" % (eventfile, outfile)

    runner.run(cmd_line)
