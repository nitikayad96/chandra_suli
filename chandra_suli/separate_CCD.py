#!/usr/bin/env python

""""
Take event file and create multiple new event files separated by CCD

command from CIAO: dmcopy filtered_event.fits[EVENTS][ccd_id=N] out.fits clobber=yes

Make sure CIAO is running before running this script
"""

import subprocess
import argparse
import os

from chandra_suli import work_within_directory


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Create new event files separated by CCD')

    parser.add_argument('--evtfile',help="Event file name", type=str, required=True)

    parser.add_argument('--indir', help = "Directory that event file is in", type=str, required=False, default='.')


    args = parser.parse_args()

    # Transform the input directory using its absolute path, expand environment variables which might
    # have been used by the user, and expand the "~" (if needed)
    evt_abspath = os.path.abspath(os.path.expandvars(os.path.expanduser(args.indir)))

    #check that directory exists
    if not os.path.exists(evt_abspath):

        raise IOError("Input dir %s does not exist!" % evt_abspath)

    with work_within_directory.work_within_directory(evt_abspath):

        for ccd_id in xrange(10):

            cmd_line = "dmcopy %s[EVENTS][ccd_id=%s] ccd_%s_%s clobber=yes" %(args.evtfile, ccd_id, ccd_id, args.evtfile)
            subprocess.check_call(cmd_line,shell=True)












