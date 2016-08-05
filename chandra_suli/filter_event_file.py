#!/usr/bin/env python

"""
Take evt3 file and use region files to subtract off sources that are already known - image will have lots of holes

Make sure CIAO is running before running this script

below = code used by Giacomo to create filtered image
ftcopy 'acisf00635_000N001_evt3.fits[EVENTS][regfilter("my_source.reg")]' test.fits

code that works with CIAO
dmcopy "acisf00635_000N001_evt3.fits[exclude sky=region(acisf00635_000N001_r0101_reg3.fits)]" filter_test.fits opt=all
"""

import argparse
import subprocess
import os
import warnings
import sys
import astropy.io.fits as pyfits
import numpy as np
import glob
import re

from chandra_suli import sanitize_filename
from chandra_suli import query_region_db
from chandra_suli import find_files


def is_variable(tsv_file, name_of_the_source):

    # Read data from tsv file
    tsv_data = np.array(np.recfromtxt(tsv_file, delimiter='\t', skip_header=11,names=True), ndmin=1)

    # Make sure data is vectorized
    if len(tsv_data.shape) == 0:

        tsv_data = np.array([tsv_data])

    tsv_names = tsv_data['name'].tolist()

    # Find index of source in question
    idx = tsv_names.index(name_of_the_source)

    # See if associated var_flag is True (some are strings with spaces, some are bools)
    if str(tsv_data['var_flag'][idx]) == "TRUE" or str(tsv_data['var_flag'][idx]) == " TRUE":

        return True


def cross_match(region_files_db, region_files_obsid):

    # Get the names of all the sources contained respectively in the OBSID catalog and in the DB catalog

    names_obsid = map(lambda x: re.match('(.+)/(CXOJ.+)/.+', x).groups()[1], region_files_obsid)

    names_db = map(lambda x: re.match('(.+)/(CXOJ.+)/.+', x).groups()[1], region_files_db)

    # Loop over all sources in the OBSID catalog, and remove them from teh DB catalog. At the end,
    # the union between the OBSID catalog and the remaining of the DB catalog will give the
    # complete catalog

    for source in names_obsid:

        try:

            index = names_db.index(source)

            if args.debug:
                print names_db[index]

            names_db.pop(index)

        except ValueError:

            warnings.warn("Source %s is in the OBSID catalog but not in the DB catalog" % source)

        else:

            if args.debug:

                print region_files_db[index]

            region_files_db.pop(index)


    cleaned_regions = list(region_files_obsid)

    cleaned_regions.extend(region_files_db)

    return cleaned_regions



if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Filter known sources out of event file')

    parser.add_argument('--evtfile', help="Name of the event file", type=str, required=True)

    parser.add_argument('--region_dir', help="Directory containing the regions file for this obsid",
                        type=str, required=True)

    parser.add_argument('--tsvfile', help="Name of TSV file", type=str, required=True)

    parser.add_argument('--outfile', help="Name of the output (filtered) event file", type=str, required=True)

    parser.add_argument("--debug", help="Debug mode (yes or no)", type=bool, required=False, default=False)

    parser.add_argument("--emin",help="Minimum energy (eV)",type=int,required=True)

    parser.add_argument("--emax",help="Maximum energy (eV)",type=int,required=True)

    parser.add_argument("--adj_factor",
                        help="If region files need to be adjusted, what factor to increase axes of ellipses by",
                        type=float, required=True)


    # assumption = all level 3 region files and event file are already downloaded into same directory

    args = parser.parse_args()

    #creates text file with name of all level 3 region files for given Obs ID

    region_dir = sanitize_filename.sanitize_filename(args.region_dir)

    obsid = os.path.split(region_dir)[-1]

    # region_dir is specific to one obsid. Get general region repository where db is located

    db_dir = os.path.split(region_dir)[0]

    # Get the region files from this observation

    region_files_obsid = find_files.find_files(region_dir, "*reg3.fits.gz")

    # Get the pointing from the event file

    evtfile = sanitize_filename.sanitize_filename(args.evtfile)

    with pyfits.open(evtfile) as f:

        ra_pnt = f['EVENTS'].header.get("RA_PNT")
        dec_pnt = f['EVENTS'].header.get("DEC_PNT")

    # Query a region of 30 arcmin, which should always cover the whole Chandra field of view,
    # to get the regions from the database

    region_files_db = query_region_db.query_region_db(ra_pnt, dec_pnt, 30.0, db_dir)

    # Now cross match the regions we got from the DB with the regions we got from this obsid
    # We try to use the information relative to this obsid as much as possible, but if there is no
    # info on a given source in this obsid we take it from the db

    region_files = cross_match(region_files_db, region_files_obsid)

    n_reg = len(region_files)

    # Loop over the region files and filter out the corresponding events

    temp_files = []

    for region_id, region_file in enumerate(region_files):

        sys.stderr.write("\rProcessing region %s out of %s ..." % (region_id+1, len(region_files)))

        temp_file = '__%d_reg_revised.fits' % (region_id)

        # Remove the file if existing
        if os.path.exists(temp_file):

            os.remove(temp_file)

        cmd_line = 'dmcopy %s[SRCREG][SHAPE=Ellipse] %s clobber=yes' % (region_file, temp_file)

        if args.debug:

            print(cmd_line)

        subprocess.check_call(cmd_line, shell=True)

        # Fix the column format, if needed

        cmd_line = "fcollen '%s' X 1" % temp_file
        subprocess.check_call(cmd_line, shell=True)

        cmd_line = "fcollen '%s' Y 1" % temp_file
        subprocess.check_call(cmd_line, shell=True)

        # Adjust the size of the ellipse, if this source is variable

        # Get the name of the source
        # Filenames are absolute paths like
        # /home/giacomov/science/chandra_transients/catalog/region_files/635/CXOJ162659.0-243557/[filename]
        # so the second-last element is the name of the source

        source_name = os.path.basename(os.path.split(region_file)[-2])
        source_name = source_name[0:3]+" "+source_name[3::]

        ##########################
        # Crossmatch with tsv file
        ##########################

        try:

            if is_variable(args.tsvfile, source_name) == True:

                # open the file with "mode='update'"

                with pyfits.open(temp_file, mode='update', memmap=False) as reg:

                    reg['SRCREG'].data.R = args.adj_factor * reg['SRCREG'].data.R

                # adjust the size of both axis by a factor (another argument)

        except ValueError:

            pass

        temp_files.append(temp_file)

    sys.stderr.write("Done\n")

    # Write all the temp files in a text file, which will be used by dmmerge
    regions_list_file = "__all_regions_list.txt"

    with open(regions_list_file, "w+") as f:

        for temp_file in temp_files:

            f.write("%s\n" % temp_file)

    # Merge all the region files

    print("Merging region files...")

    all_regions_file = '%s_all_regions.fits' %(obsid)

    cmd_line = 'fmerge @%s %s clobber=yes' % (regions_list_file, all_regions_file)

    if args.debug:

        print(cmd_line)

    subprocess.check_call(cmd_line, shell=True)

    # Now fix the COMPONENT column (each region must be a different component, otherwise
    # dmcopy will crash)

    fits_file = pyfits.open(all_regions_file, mode='update',memmap=False)

    fits_file['SRCREG'].data.COMPONENT[:] = range(fits_file['SRCREG'].data.shape[0])

    fits_file.close()

    # Finally filter the file

    print("Filtering event file...")

    # Remove the outfile if existing
    if os.path.exists(args.outfile):

        os.remove(args.outfile)

    # first filter regions out, create temp file

    temp_filter = '__temp__%s' %args.outfile

    cmd_line = 'dmcopy \"%s[exclude sky=region(%s)]\" ' \
               '%s opt=all clobber=yes' % (args.evtfile, all_regions_file, temp_filter)

    if args.debug:

        print(cmd_line)

    subprocess.check_call(cmd_line, shell=True)

    cmd_line = 'dmcopy %s[energy=%d:%d] %s opt=all clobber=yes' %(temp_filter, args.emin, args.emax, args.outfile)

    if args.debug:

        print(cmd_line)

    subprocess.check_call(cmd_line, shell=True)

    # TODO: remove files
    files_to_remove = glob.glob("__*")

    if not args.debug:

        for file in files_to_remove:

            os.remove(file)

    else:

        print("\n\nWARNING: did not remove temporary files because we are in debug mode")