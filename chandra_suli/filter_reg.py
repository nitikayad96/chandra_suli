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

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Filter known sources out of level 3 event file')
    parser.add_argument("--obsid",help="Observation ID Numbers",nargs='+',type=int,required=True)

    # assumption = all level 3 region files and event file are already downloaded into same directory

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

        #create new region file containing only first row of source region block
        #eliminate dealing with problematic regions
        #ex. entire CCD being chosen as a region
        subprocess.call('dmcopy %s[SRCREG][#row=1] %d_%d_reg_revised.fits clobber=yes' % (reg,i,0), shell=True)

        # Create initial filtered file, subtracting first region from original event file
        #get compressed event file from folder with title as the ObsID
        subprocess.call('dmcopy \"%d/*%d*evt3.fits.gz[exclude sky=region(%d_%d_reg_revised.fits)]\"'
                        '%d_filtered_0.fits opt=all clobber=yes' %(i,i,i,0,i), shell=True)

        #delete initial revised region file
        subprocess.call('rm %d_%d_reg_revised.fits' % (i, 0), shell=True)


        #loop through rest of region files
        for j in range(1,int(n_reg)-1):

            #read in next line of text file
            reg = f.readline()[:-1]

            print j
            print reg

            #create new region file containing only first row of source region block
            subprocess.call('dmcopy %s[SRCREG][#row=1] %d_%d_reg_revised.fits clobber=yes' % (reg,i,j), shell=True)

            #create changes to each new file so by the end of loop, all changes will be compiled in one file
            subprocess.call('dmcopy \"%d_filtered_%d.fits[exclude sky=region(%d_%d_reg_revised.fits)]\" '
                            '%d_filtered_%d.fits opt=all clobber=yes'
                            % (i,j-1,i,j,i,j), shell=True)

            #delete old files as new ones are created to save storage space
            subprocess.call('rm %d_filtered_%d.fits' %(i,j-1),shell=True)
            subprocess.call('rm %d_%d_reg_revised.fits' %(i,j),shell=True)

        #rename final file into format obsid_filtered.fits
        subprocess.call('mv %d_filtered_%d.fits %d_filtered.fits' %(i,j,i),shell=True)

        #closes text file
        f.close()






