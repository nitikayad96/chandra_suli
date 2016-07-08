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

    parser = argparse.ArgumentParser(description="Take output from Bayesian block algorithm and cross match with "
                                                 "previously flagged variable sources")
    parser.add_argument("--bbfile",help="Path of input text file",required=True)
    parser.add_argument("--tsvfile",help="Path of tsv file",required=True)
    parser.add_argument("--outfile", help="Path of out file", required=True)

    args = parser.parse_args()

    # get directory path and file name from input file arguments

    bb_file_path = os.path.abspath(os.path.expandvars(os.path.expanduser(args.bbfile)))
    tsv_file_path = os.path.abspath(os.path.expandvars(os.path.expanduser(args.tsvfile)))

    # read BB data into array
    bb_data = np.array(np.recfromtxt(bb_file_path,names=True), ndmin=1)

    # number of rows of data
    bb_n = len(bb_data)

    # read tsv data into array
    tsv_data = np.recfromtxt(tsv_file_path, delimiter='\t', skip_header=11,names=True)

    # Filter out all non-variable sources

    variability = np.array(map(lambda x:x.replace(" ","") == "TRUE", tsv_data['var_flag']))

    idx = (variability == True)

    variable_sources = tsv_data[idx]

    with open(args.outfile,"w") as f:

        # Pre-existing column names
        existing_column_names = " ".join(bb_data.dtype.names)

        f.write("# %s Closest_Variable_Source Distance\n" % existing_column_names)

        if variable_sources.shape[0] == 0:

            # No variable source in the catalog. Let's add a "None" for each entry in the new columns

            for i in xrange(bb_n):

                temp_list = []

                for j in xrange(len(bb_data.dtype.names)):

                    temp_list.append(str(bb_data[i][j]))

                temp_list.append("None")
                temp_list.append("-1")

                line = " ".join(temp_list)

                f.write("%s\n" % line)

        else:

            # There are variable sources in the catalog

            # Get their coordinates

            tsv_ra = variable_sources['ra']
            tsv_dec = variable_sources['dec']

            for i in xrange(bb_n):

                # Get the coordinate of the candidate transient

                bb_ra = bb_data[i]['RA']
                bb_dec = bb_data[i]['Dec']

                # Compute angular distance between the candidate transient and all variable sources

                distances = angular_distance.angular_distance(tsv_ra,tsv_dec,bb_ra,bb_dec, unit='arcsec')

                # Get the position of the minimum distance

                idx_min = np.argmin(distances)

                # Get the name of the closest variable source

                src_name = variable_sources['name'][idx_min]

                # Replace any space in the name with an underscore
                src_name = src_name.replace(" ","_")

                temp_list = []

                for j in xrange(len(bb_data.dtype.names)):

                    temp_list.append(str(bb_data[i][j]))

                # Fill the column "Closest_Variable_Source" with the name of the source

                temp_list.append(src_name)

                # Fill the column with the angular distance

                temp_list.append(str(distances[idx_min]))

                line = " ".join(temp_list)

                f.write("%s\n" % line)













