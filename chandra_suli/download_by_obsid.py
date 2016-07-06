#!/usr/bin/env python

"""
Download Level 3 Event File (evt3) and list of Source Names/RA/DEC/Off-Axis Angle/
Flags for Extended and Variable Sources given inputs of Observation IDs

Make sure CIAO is running before running this script
"""

import subprocess
import argparse
import os

from chandra_suli import find_files

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Download event files and exposure map from the Chandra catalog')
    parser.add_argument("--obsid",help="Observation ID Numbers",nargs='+',type=int,required=True)
    parser.add_argument("--outdir",help="Directory where to put the output",required=False,
                        default='.')
    # default directory = current one

    args = parser.parse_args()

    for this_obsid in args.obsid:

        #Download exposure map
        subprocess.check_call("obsid_search_csc obsid=%d download=all outfile=%d.tsv filetype=exp "
                "root=%s mode=h clobber=yes verbose=1 "
                "columns=m.ra,m.dec,o.theta,m.extent_flag,m.var_flag" % (this_obsid, this_obsid, args.outdir), shell=True)

        #Downlaod level 2 event files (evt2)
        cmd_line = "download_chandra_obsid %d evt2" %(this_obsid)
        subprocess.check_call(cmd_line, shell=True)

        #Move evt2 file and .tsv file to same directory as exposure map

        outdir_path = os.path.abspath(os.path.expandvars(os.path.expanduser(args.outdir)))

        # get paths of files
        evt2 = find_files.find_files(os.getcwd(),'*evt2.fits.gz')[0]
        tsv = find_files.find_files(os.getcwd(),"%d.tsv" %this_obsid)[0]

        #move evt2 file and delete empty directories
        os.rename("%s" % (evt2),"%s/%d/%d_evt2.fits.gz" % (outdir_path, this_obsid, this_obsid))
        os.rmdir("%d/primary" % (this_obsid))
        os.rmdir("%d" % (this_obsid))

        #move tsv file
        os.rename(tsv, "%s/%d.tsv" %(outdir_path, this_obsid))




