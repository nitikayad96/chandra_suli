#!/usr/bin/env python

"""
Take output from Bayesian block algorithm and cross check matches with previously flagged variable X-ray sources

Note about BB file:
Column 1/2 = RA/Dec
Column 3/4 = Tstart/Tstop
Column 5 = Probability
"""

import argparse
import numpy as np
import os
from chandra_suli import work_within_directory
from chandra_suli import angular_distance

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Take output from Bayesian block algorithm and cross match with"
                                                 "previously flagged variable sources")
    parser.add_argument("--bbfile",help="Path of input text file",required=True)
    parser.add_argument("--tsvfile",help="Path of tsv file",required=True)

    args = parser.parse_args()

    #get directory path and file name from input file arguments
    bb_dir = os.path.dirname(args.bbfile)
    bb_file = os.path.basename(args.bbfile)

    tsv_dir = os.path.dirname(args.tsvfile)
    tsv_file = os.path.basename(args.tsvfile)

    with work_within_directory.work_within_directory(bb_dir):

        # read BB data into array
        bb_data = np.recfromtxt(bb_file,names=True)

        #number of rows of data
        bb_n = len(bb_data)

        # read tsv data into array
        tsv_data = np.recfromtxt(tsv_file, delimiter='\t', skip_header=11,names=True)

        # Filter out all non-variable sources

        variability = np.array(map(lambda x:x.replace(" ","")=="TRUE", tsv_data['var_flag']))

        idx = (variability==True)

        variable_sources = tsv_data[idx]

        filename = "check_var_%s" %bb_file
        with open(filename,"w") as f:

            f.write("RA Dec Tstart  Tstop   Probability Closest_Variable_Source")
            f.write("\n")

            if variable_sources.shape[0] == 0:

                for i in xrange(bb_n):

                    temp_list = []

                    for j in xrange(5):

                        temp_list.append(str(bb_data[i][j]))

                    temp_list.append("None")
                    line = "\t".join(temp_list)
                    f.write(line)
                    f.write("\n")


            else:

                tsv_ra = variable_sources['ra']
                tsv_dec = variable_sources['dec']

                for i in xrange(bb_n):

                    bb_ra = bb_data[i]['RA']
                    bb_dec = bb_data[i]['Dec']

                    distances = angular_distance.angular_distance(tsv_ra,tsv_dec,bb_ra,bb_dec)
                    idx_min = np.argmin(distances)

                    src_name = variable_sources['name'][idx_min]

                    #for i in xrange(bb_n):

                    temp_list = []

                    for j in xrange(5):
                        temp_list.append(str(bb_data[i][j]))

                    temp_list.append(src_name)
                    line = "\t".join(temp_list)
                    f.write(line)
                    f.write("\n")













