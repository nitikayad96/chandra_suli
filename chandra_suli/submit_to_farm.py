#!/usr/bin/env python

"""
Submit one or more obsid for processing on the Stanford computer farm
"""

import argparse
import subprocess
import os

from chandra_suli.sanitize_filename import sanitize_filename
from chandra_suli.which import which
from chandra_suli.work_within_directory import work_within_directory


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Submit observation for processing on the computer farm')

    # Required parameters

    parser.add_argument("-d1", "--indir", help="Input directory containing the data", type=str, required=True)
    parser.add_argument("-d2", "--regdir", help="Input directory containing the regions", type=str, required=True)
    parser.add_argument("-d3", "--outdir", help="Directory for the output", type=str, required=True)

    # Arguments for farm_step2

    parser.add_argument("-o", "--obsid", help="Observation ID Number", type=int, required=True, nargs='+')

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

    parser.add_argument('--test', dest='test_run', action='store_true')
    parser.set_defaults(test_run=False)

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

    # Go there

    with work_within_directory(outdir):

        # Create logs directory if does not exists
        if not os.path.exists('logs'):

            os.mkdir('logs')

        # Create generated_data directory, if does not exist
        if not os.path.exists('results'):

            os.mkdir('results')

        # Generate the command line

        log_path = os.path.abspath('logs')
        out_path = os.path.abspath('results')

        # Find executable
        exe_path = which('farm_wrapper.py')


        def get_cmd_line(this_obsid):

            options = '--indir %s --regdir %s --outdir %s -o %s -a %s -e1 %s -e2 %s ' \
                      '-p %s -s %s -m %s -c %s' % (args.indir, args.regdir, out_path, args.obsid, args.adj_factor,
                                                   args.emin, args.emax, args.typeIerror, args.sigmaThreshold,
                                                   args.multiplicity, args.ncpus)

            cmd_line = "qsub -l vmem=10gb -o %s/%s.out -e %s/%s.err -V " \
                       "-F '%s' %s " %(log_path, this_obsid, log_path, this_obsid, options, exe_path)

            return cmd_line

        for obsid in args.obsid:

            this_cmd_line = get_cmd_line(obsid)

            print(this_cmd_line)

            if not args.test_run:

                subprocess.check_call(this_cmd_line, shell=True)
