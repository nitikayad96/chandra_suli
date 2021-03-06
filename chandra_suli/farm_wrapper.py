#!/usr/bin/env python

import argparse
import glob
import os
import shutil
import subprocess
import sys
import traceback

from chandra_suli.data_package import DataPackage
from chandra_suli.sanitize_filename import sanitize_filename
from chandra_suli.work_within_directory import work_within_directory


def clean_up(this_workdir):
    # First move out of the workdir
    os.chdir(os.path.expanduser('~'))

    # Now remove the directory
    try:

        shutil.rmtree(this_workdir)

    except:

        print("Could not remove workdir. Unfortunately I left behind some trash!!")
        raise

    else:

        print("Clean up completed.")


def copy_directory(data_dir, workdir):
    if data_dir[-1] == '/':
        data_dir = data_dir[:-1]

    data_dir_basename = os.path.split(data_dir)[-1]

    local_data_dir = os.path.join(workdir, data_dir_basename)

    print("Copying %s into %s..." % (data_dir, local_data_dir))

    shutil.copytree(data_dir, local_data_dir)

    return os.path.abspath(local_data_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser('Wrapper around the script farm_step2')

    # Required parameters

    parser.add_argument("-d1", "--indir", help="Input directory containing the data", type=str, required=True)
    parser.add_argument("-d2", "--regdir", help="Input directory containing the regions", type=str, required=True)
    parser.add_argument("-d3", "--outdir", help="Directory for the output", type=str, required=True)

    # Arguments for farm_step2

    parser.add_argument("-o", "--obsid", help="Observation ID Number", type=int, required=True, nargs="+")

    parser.add_argument('-a', "--adj_factor",
                        help="If region files need to be adjusted, what factor to increase axes of ellipses by",
                        type=float, required=True)

    parser.add_argument("-e1", "--emin", help="Minimum energy (eV)", type=int, required=True)

    parser.add_argument("-e2", "--emax", help="Maximum energy (eV)", type=int, required=True)

    parser.add_argument("-c", "--ncpus", help="Number of CPUs to use (default=1)",
                        type=int, default=1, required=False)

    parser.add_argument("-p", "--typeIerror",
                        help="Type I error probability for the Bayesian Blocks algorithm.",
                        type=float,
                        default=1e-5,
                        required=False)

    parser.add_argument("-s", "--sigmaThreshold",
                        help="Threshold for the final significance. All intervals found "
                             "by the bayesian blocks "
                             "algorithm which does not surpass this threshold will not be saved in the "
                             "final file.",
                        type=float,
                        default=5.0,
                        required=False)

    parser.add_argument("-m", "--multiplicity", help="Control the overlap of the regions."
                                                     " A multiplicity of 2 means the centers of the regions are"
                                                     " shifted by 1/2 of the region size (they overlap by 50 percent),"
                                                     " a multiplicity of 4 means they are shifted by 1/4 of "
                                                     " their size (they overlap by 75 percent), and so on.",
                        required=False, default=2.0, type=float)

    parser.add_argument("-v", "--verbosity", help="Info or debug", type=str, required=False, default='info',
                        choices=['info', 'debug'])

    args = parser.parse_args()

    # Check that the output dir already exists

    outdir = sanitize_filename(args.outdir)

    if not os.path.exists(outdir):
        raise IOError("You need to create the directory %s before running this script" % outdir)

    indir = sanitize_filename(args.indir)

    if not os.path.exists(indir):
        raise IOError("Input data repository %s does not exist" % indir)

    regdir = sanitize_filename(args.regdir)

    if not os.path.exists(regdir):
        raise IOError("Input region repository %s does not exist" % regdir)

    # First step of a farm job: Stage-in

    # Create a work directory in the local disk on the node

    # This is your unique job ID (a number like 546127)
    unique_id = os.environ.get("PBS_JOBID").split(".")[0]

    # os.path.join joins two path in a system-independent way
    workdir = os.path.join('/dev/shm', unique_id)

    # Now create the workdir
    print("About to create %s..." % (workdir))

    try:
        os.makedirs(workdir)
    except:
        print("Could not create workdir %s !!!!" % (workdir))
        raise
    else:
        # This will be executed if no exception is raised
        print("Successfully created %s" % (workdir))

    cmd_line = "didn't even reach the command line execution"

    for this_obsid in args.obsid:

        # now you have to go there
        with work_within_directory(workdir):

            try:

                # copy parameter files into this directory to avoid any glitches with the NFS

                par_files = glob.glob(os.path.join(os.path.expanduser('~/pfiles'), '*.par'))

                for par_file in par_files:
                    shutil.copy(par_file, workdir)

                # Execute job

                cmd_line = "farm_step2.py -d %s --obsid %s --region_repo %s --adj_factor %s " \
                           "--emin %s --emax %s --ncpus %s --typeIerror %s --sigmaThreshold %s " \
                           "--multiplicity %s --verbosity %s" % (indir, this_obsid, args.regdir, args.adj_factor,
                                                                 args.emin, args.emax, args.ncpus,
                                                                 args.typeIerror, args.sigmaThreshold,
                                                                 args.multiplicity,
                                                                 args.verbosity)

                # Do whathever
                print("\n\nAbout to execute command:")
                print(cmd_line)
                print('\n')

                subprocess.check_call(cmd_line, shell=True)

            except:

                traceback.print_exc()

                print(sys.exc_info())

                print("Cannot execute command: %s" % cmd_line)
                print("Maybe this will help:")
                print("\nContent of directory:\n")

                subprocess.check_call("ls", shell=True)

                print("\nFree space on disk:\n")
                subprocess.check_call("df . -h", shell=True)

            else:

                # Stage-out

                print("\n\nStage out\n\n")

                output_package = DataPackage(this_obsid)

                output_package.copy_to(outdir)

            finally:

                # This is executed in any case, whether an exception have been raised or not
                # I use this so we are sure we are not leaving trash behind even
                # if this job fails

                clean_up(workdir)
