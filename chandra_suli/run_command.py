import subprocess


class CommandRunner(object):

    def __init__(self, logger):

        self._logger = logger

    def run(self, cmd_line):

        self._logger.info(cmd_line)

        subprocess.check_call(cmd_line, shell=True)