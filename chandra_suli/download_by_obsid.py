#!/usr/bin/env python

"""
Download Level 3 Event File (evt3) and list of Source Names/RA/DEC/Off-Axis Angle/
Flags for Extended and Variable Sources given inputs of Observation IDs

Make sure CIAO is running before running this script
"""

import subprocess
import argparse
import os

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Download EVT3 Files')
    parser.add_argument("--obsid",help="Observation ID Numbers",nargs='+',type=int,required=True)
    parser.add_argument("--outdir",help="Directory where to put the output",required=False,
                        default='.')
    # default directory = current one

    args = parser.parse_args()

    for i in args.obsid:

        subprocess.call("obsid_search_csc obsid=%d download=all outfile=%d.tsv filetype=evt "
                "root=%s mode=h clobber=yes verbose=1 "
                "columns=m.ra,m.dec,o.theta,m.extent_flag,m.var_flag" % (i, i, args.outdir), shell=True)

