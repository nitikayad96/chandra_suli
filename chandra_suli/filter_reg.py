#!/usr/bin/env python

"""
Take evt3 file and use region files to subtract off sources that are already known - image will have lots of holes

Make sure CIAO is running before running this script

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

        #creates text file with name of all level 3 region files for given Obs ID
        subprocess.call("find %d -name \"*reg3.fits.gz\" > %d_reg.txt" %(i, i), shell=True)

        #counts number of region files for given Obs ID by counting number of folders in Obs ID directory
        proc = subprocess.Popen('find %d -type d | wc -l' %i,shell=True,stdout=subprocess.PIPE)
        n_reg = proc.communicate()[0]

        #open text file created above for reading
        f = open('%d_reg.txt' %i,'r')

        # read first region file name from text file - note: last character in each line is a space, so is omitted
        reg = f.readline()[:-1]

        # Create initial filtered file, subtracting first region from original event file
        subprocess.call('dmcopy \"*%d*evt3.fits[exclude sky=region(%s)]\" %d_filtered_0.fits opt=all' %(i, reg, i),
                        shell=True)

        #for j in range(1,n_reg)

        #closes text file
        f.close()






