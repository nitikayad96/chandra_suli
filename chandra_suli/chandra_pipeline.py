#!/usr/bin/env python

"""
Script to produce an output file of possible transients in one step

File will be saved in directory from which code is run
"""

import argparse
import os
import subprocess
import warnings
import shutil
import sys
import astropy.io.fits as pyfits
import glob

from chandra_suli import work_within_directory
from chandra_suli import find_files

if __name__=="__main__":


    parser = argparse.ArgumentParser(description='Create a text file summarizing possible transient sources')

    parser.add_argument("--obsid",help="Observation ID Numbers", type=int, required=True)
    parser.add_argument("--debug", help="Debug mode (yes or no)", type=bool, required=False, default=False)

    # DOWNLOAD OBSERVATION FILES

    # default directory = current one

    args = parser.parse_args()

    temp_dir = "__temp"

    if not os.path.exists(temp_dir):

        os.makedirs("__temp")

    else:

        warnings.warn("The directory %s already exists" % temp_dir)

    with work_within_directory.work_within_directory(temp_dir):

        # Download exposure map

        cmd_line = ("obsid_search_csc obsid=%d download=all outfile=%d.tsv filetype=exp "
                    "mode=h clobber=yes verbose=1 "
                    "columns=m.ra,m.dec,o.theta,m.extent_flag,m.var_flag"
                    % (args.obsid, args.obsid))

        subprocess.check_call(cmd_line, shell=True)

        # Downlaod level 2 event files (evt2)
        cmd_line = "download_chandra_obsid %d evt2" %(args.obsid)

        subprocess.check_call(cmd_line, shell=True)

    # Move evt2 file and .tsv file to same directory as exposure map

    # get paths of files
    evt2 = find_files.find_files(os.getcwd(),'*evt2.fits.gz')[0]
    tsv = find_files.find_files(os.getcwd(),"%d.tsv" %args.obsid)[0]
    exp = find_files.find_files(os.getcwd(),"*exp3.fits.gz")[0]

    # move evt2 file and delete empty directories

    for this_file in [evt2, tsv, exp]:

        os.rename(this_file,os.path.basename(this_file))

    shutil.rmtree(temp_dir)

    evtfile = os.path.basename(evt2)

    # FILTER REGIONS

    #creates text file with name of all level 3 region files for given Obs ID

    region_files = find_files.find_files('.', "*reg3.fits.gz")

    n_reg = len(region_files)

    # Loop over the region files and filter out the corresponding events

    temp_files = []

    for region_id, region_file in enumerate(region_files):

        sys.stderr.write("\rProcessing region %s out of %s ..." % (region_id + 1, len(region_files)))

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

        temp_files.append(temp_file)

    sys.stderr.write("Done\n")

    # Write all the temp files in a text file, which will be used by dmmerge
    regions_list_file = "__all_regions_list.txt"

    with open(regions_list_file,"w+") as f:

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

    evtfile_filtered = "%d_filtered.fits" % args.obsid

    # Remove the outfile if existing

    if os.path.exists(evtfile_filtered):

        os.remove(evtfile_filtered)

    cmd_line = 'dmcopy \"%s[exclude sky=region(%s)]\" ' \
               '%s opt=all clobber=yes' % (evtfile, all_regions_file, evtfile_filtered)

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

    # SEPARATE BY CCD

    print("Separating by CCD...")

    for ccd_id in xrange(10):

        ccd_file = "%d_filtered_ccd_%s.fits" %(args.obsid, ccd_id)

        cmd_line = "dmcopy %s[EVENTS][ccd_id=%s] %s clobber=yes" \
                   % (evtfile_filtered, ccd_id, ccd_file)

        subprocess.check_call(cmd_line, shell=True)

        # check if certain CCD files are empty and then delete them if so

        f = pyfits.open("%s" %(ccd_file))
        ccd_data = f[1].data

        if len(ccd_data)==0:

            os.remove(ccd_file)

        f.close()





