#!/usr/bin/env python

"""
Create the database of the regions, containing the R.A,Dec of each source and the path to its region file
"""

import argparse
import collections
import os
import re
import sys

import fitsio

from chandra_suli import find_files
from chandra_suli import work_within_directory
from chandra_suli.logging_system import get_logger
from chandra_suli.sanitize_filename import sanitize_filename

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create source database')

    parser.add_argument('--region_dir', help="Directory containing the regions file for this obsid",
                        type=str, required=True)

    parser.add_argument('--outfile', help="Name of the output (filtered) event file", type=str, required=True)

    parser.add_argument("--debug", help="Debug mode (yes or no)", type=bool, required=False, default=False)

    # assumption = all level 3 region files and event file are already downloaded into same directory, the region_dir

    args = parser.parse_args()

    region_dir = sanitize_filename(args.region_dir)

    log = get_logger("create_regions_db")

    with work_within_directory.work_within_directory(region_dir):

        # Find all region files
        region_files = find_files.find_files('.', '*_reg3.fits.gz')

        log.info("Found %s region files" % len(region_files))

        db = collections.OrderedDict()

        for i, region_file in enumerate(region_files):

            sys.stderr.write("\r%s out of %s" % (i + 1, len(region_files)))

            header = fitsio.read_header(region_file, "SRCREG")

            ra = header['RA']
            dec = header['DEC']
            obsid = header['OBS_ID']

            # with pyfits.open(region_file) as f:
            #
            #     ra = f['SRCREG'].header.get("RA")
            #     dec = f['SRCREG'].header.get("DEC")
            #     obsid = f['SRCREG'].header.get("OBS_ID")

            assert ra is not None, "Cannot find R.A. in file %s" % region_file
            assert dec is not None, "Cannot find Dec. in file %s" % region_file
            assert obsid is not None, "Cannot find OBSID in file %s" % region_file

            try:

                ra = float(ra)
                dec = float(dec)

            except:

                raise RuntimeError("Cannot convert coordinates (%s,%s) to floats" % (ra, dec))

            try:

                obsid = int(obsid)

            except:

                raise RuntimeError("Cannot convert obsid %s to integer" % obsid)

            # Get the source name from the path

            try:

                g = re.match('(.+)/(CXOJ.+)/.+', region_file)

                name = g.groups()[1]

            except:

                raise RuntimeError("Cannot figure out the name of the source from the path %s" % (region_file))

            db[name] = (ra, dec, obsid, os.path.relpath(region_file))

    sys.stderr.write("done\n")

    # Write the outfile

    outfile = sanitize_filename(args.outfile)

    with open(outfile, 'w+') as f:

        f.write("#NAME RA DEC OBSID REGION_FILE\n")

        for source_name in db:
            ra, dec, obsid, region_file = db[source_name]

            f.write("%s %.5f %.5f %i %s\n" % (source_name, ra, dec, obsid, region_file))
