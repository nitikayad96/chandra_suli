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
import sys
import astropy.io.fits as pyfits
import glob

from chandra_suli import find_files


def is_variable(tsv_file, name_of_the_source):

    # open the file

    # fix the case for one line

    pass


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Filter known sources out of event file')

    parser.add_argument('--evtfile',help="Name of the event file", type=str, required=True)

    parser.add_argument('--region_dir', help="Directory containing the regions file for this obsid",
                        type=str, required=True)

    parser.add_argument('--outfile', help="Name of the output (filtered) event file", type=str, required=True)

    parser.add_argument("--debug", help="Debug mode (yes or no)", type=bool, required=False, default=False)

    parser.add_argument("--emin",help="Minimum energy (eV)",type=int,required=True)

    parser.add_argument("--emax",help="Maximum energy (eV)",type=int,required=True)


    # assumption = all level 3 region files and event file are already downloaded into same directory

    args = parser.parse_args()

    #creates text file with name of all level 3 region files for given Obs ID

    region_files = find_files.find_files(args.region_dir, "*reg3.fits.gz")

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

        source_name = os.path.split(region_file)[-2]

        ##########################
        # Crossmatch with tsv file
        ##########################

        if is_variable():

            # open the file with "mode='update'"

            with pyfits.open(region_file, mode='update'):

                pass

            # adjust the size of both axis by a factor (another argument)


        temp_files.append(temp_file)

    sys.stderr.write("Done\n")

    # Write all the temp files in a text file, which will be used by dmmerge
    regions_list_file = "__all_regions_list.txt"

    with open(regions_list_file, "w+") as f:

        for temp_file in temp_files:

            f.write("%s\n" % temp_file)

    # Merge all the region files

    print("Merging region files...")

    all_regions_file = '__all_regions.fits'

    cmd_line = 'dmmerge @%s %s clobber=yes mode=h' % (regions_list_file, all_regions_file)

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