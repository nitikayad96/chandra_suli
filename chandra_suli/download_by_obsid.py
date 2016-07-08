#!/usr/bin/env python

"""
Download Level 3 Event File (evt3) and list of Source Names/RA/DEC/Off-Axis Angle/
Flags for Extended and Variable Sources given inputs of Observation IDs

Make sure CIAO is running before running this script
"""

import argparse
import os
import subprocess
import warnings
import shutil

import work_within_directory
from chandra_suli import find_files

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Download event files and exposure map from the Chandra catalog')
    parser.add_argument("--obsid",help="Observation ID Numbers", type=int, required=True)

    # default directory = current one

    args = parser.parse_args()

    temp_dir = "__temp"

    if not os.path.exists(temp_dir):

        os.makedirs("__temp")

    else:

        warnings.warn("The directory %s already exists" % temp_dir)

    with work_within_directory.work_within_directory(temp_dir):

        #Download exposure map

        cmd_line = ("obsid_search_csc obsid=%d download=all outfile=%d.tsv filetype=exp "
                    "mode=h clobber=yes verbose=1 "
                    "columns=m.ra,m.dec,o.theta,m.extent_flag,m.var_flag"
                    % (args.obsid, args.obsid))

        subprocess.check_call(cmd_line, shell=True)

        #Downlaod level 2 event files (evt2)
        cmd_line = "download_chandra_obsid %d evt2" %(args.obsid)

        subprocess.check_call(cmd_line, shell=True)

    #Move evt2 file and .tsv file to same directory as exposure map

    # get paths of files
    evt2 = find_files.find_files(os.getcwd(),'*evt2.fits.gz')[0]
    tsv = find_files.find_files(os.getcwd(),"%d.tsv" %args.obsid)[0]
    exp = find_files.find_files(os.getcwd(),"*exp3.fits.gz")[0]

    #move evt2 file and delete empty directories

    for this_file in [evt2, tsv, exp]:

        os.rename(this_file,os.path.basename(this_file))

    shutil.rmtree(temp_dir)

    evtfile = os.path.basename(evt2)
    expfile = os.path.basename(exp)
    tsvfile = os.path.basename(tsv)



