#!/usr/bin/env python

"""
Take evt3 file and use region files to subtract off sources that are already known - image will have lots of holes
Goals by Friday 6/31 - Get script working for one image at a time

below = code used by Giacomo to create filtered image
ftcopy 'acisf00635_000N001_evt3.fits[EVENTS][regfilter("my_source.reg")]' test.fits

code that works with CIAO
dmcopy "acisf00635_000N001_evt3.fits[exclude sky=region(acisf00635_000N001_r0101_reg3.fits)]" filter_test.fits opt=all
"""

import argparse
import subprocess
import os

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Filter known sources out of level 3 event file')
    parser.add_argument("--obsid",help="Observation ID Numbers",nargs='+',type=int,required=True)

    # assumption = all region files and event files are already downloaded into same directory

    args = parser.parse_args()

    #changes me from chandra_suli folder up three levels to VM_shared folder, where evt3 and reg3 files are held
    os.chdir("../../../")

    for i in args.obsid:

        subprocess.call("find %d -name \"*reg3.fits.gz\" > %d_reg.txt" %(i,i), shell=True)



