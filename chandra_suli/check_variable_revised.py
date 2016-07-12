#!/usr/bin/env python


import argparse
import numpy as np
import sys
import os
from chandra_suli import work_within_directory
from chandra_suli import angular_distance
from chandra_suli.run_command import CommandRunner
from chandra_suli import logging_system


if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Take output from Bayesian block algorithm and cross match with "
                                                 "previously flagged variable sources")
    parser.add_argument("--bbfile",help="Path of input text file",required=True)
    parser.add_argument("--outfile", help="Path of out file", required=True)
    parser.add_argument("--radius",help="Radius in arcmin in which to check for variables",
                        type=int, required=False, default=1)

    # Get logger for this command

    logger = logging_system.get_logger(os.path.basename(sys.argv[0]))

    # Instance the command runner

    runner = CommandRunner(logger)

    args = parser.parse_args()

    # get directory path and file name from input file arguments

    bb_file_path = os.path.abspath(os.path.expandvars(os.path.expanduser(args.bbfile)))

    # read BB data into array
    bb_data = np.array(np.recfromtxt(bb_file_path,names=True), ndmin=1)

    # number of rows of data
    bb_n = len(bb_data)

    with open(args.outfile, "w") as f:

        # Pre-existing column names
        existing_column_names = " ".join(bb_data.dtype.names)

        f.write("# %s Closest_Variable_Source Separation(arcsec) Obsid\n" % existing_column_names)

        for i in xrange(bb_n):

            ra = bb_data['RA'][i]
            dec = bb_data['Dec'][i]

            temp_file = "__var_sources.tsv"
            cmd_line = "search_csc %s,%s radius=%s outfile=%s columns=m.var_flag" %(ra,dec,args.radius,temp_file)
            runner.run(cmd_line)

            tsv_data = np.recfromtxt(temp_file, delimiter='\t', skip_header=10, names=True)

            # Filter out all non-variable sources

            variability = np.array(map(lambda x: x.replace(" ", "") == "TRUE", tsv_data['var_flag']))

            idx = (variability == True)

            variable_sources = tsv_data[idx]

            # Find source with minimum separation

            if variable_sources.shape[0] == 0:

                # No variable source in the catalog. Let's add a "None" for each entry in the new columns

                temp_list = []

                for j in xrange(len(bb_data.dtype.names)):
                    temp_list.append(str(bb_data[i][j]))

                # Fill the columns "Closest_Variable_Source","Separation","Obsid" with appropriate info

                temp_list.append("None")
                temp_list.append(str(-1))
                temp_list.append(str(0))

                line = " ".join(temp_list)

                f.write("%s\n" % line)

                os.remove(temp_file)


            else:

                idx_min = np.argmin(variable_sources['sepn'])

                # Get the name/separation/obsid of the closest variable source

                src_name = variable_sources['name'][idx_min]
                src_sepn = variable_sources['sepn'][idx_min]
                src_obsid = variable_sources['obsid'][idx_min]

                # Replace any space in the name with an underscore
                src_name = src_name.replace(" ", "_")

                temp_list = []

                for j in xrange(len(bb_data.dtype.names)):

                    temp_list.append(str(bb_data[i][j]))

                # Fill the columns "Closest_Variable_Source","Separation","Obsid" with appropriate info

                temp_list.append(src_name)
                temp_list.append(str(src_sepn))
                temp_list.append(str(src_obsid))

                line = " ".join(temp_list)

                f.write("%s\n" % line)

                os.remove(temp_file)











