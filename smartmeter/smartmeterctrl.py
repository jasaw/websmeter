""" Controls the Ember smart meter """

import sys
import exceptions
import subprocess
import fcntl
import select
import os
import signal

import logger
import error
import zb_key_mgr
import zb_nwk_mgr
import zb_drlc_mgr
import zb_diag_mgr


class Error(error.Generic):
    """Base class for smartmeter ctrl module exceptions"""
    pass

class UsageError(Error):
    """Process error"""
    pass

class ProcError(Error):
    """Process error"""
    pass


class SmartMeterCtrl(object):

    def __init__(self, bin_path, device_path):
        self.logger = logger.Logger('smctrl')
        self.bin_path = bin_path
        self.device_path = device_path
        self.sm_proc = None
        self.commands = [];
        self.rsp_listeners = [];
        self.cmd_generators = [];
        self.key_mgr = zb_key_mgr.ZbKeyMgr()
        self.nwk_mgr = zb_nwk_mgr.ZbNwkMgr()
        self.drlc_mgr = zb_drlc_mgr.ZbDrlcMgr()
        self.diag_mgr = zb_diag_mgr.ZbDiagMgr()
        self.rsp_listeners.append(self.key_mgr)
        self.rsp_listeners.append(self.nwk_mgr)
        self.rsp_listeners.append(self.drlc_mgr)
        self.rsp_listeners.append(self.diag_mgr)
        self.cmd_generators.append(self.key_mgr)
        self.cmd_generators.append(self.nwk_mgr)
        self.cmd_generators.append(self.drlc_mgr)
        self.cmd_generators.append(self.diag_mgr)

    def __del__(self):
        self.terminate = True
        if self.sm_proc is not None:
            self.sm_proc.terminate()

    def __make_nonblock(self, pipe):
        fd = pipe.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def __read_all_from_pipe(self, pipe, lines=''):
        lines = lines + pipe.read(4096)
        return lines

    def __process_sm_stdout(self):
        """read and process smartmeter stdout"""
        self.sm_stdout_lines = self.__read_all_from_pipe(self.sm_proc.stdout, self.sm_stdout_lines[-1]).split('\n')
        rsp = self.sm_stdout_lines[:-1]
        self.sm_stdout_lines = self.sm_stdout_lines[-1:]
        for line in rsp:
            # DEBUG: remove this print
            self.logger.log('sm: %s', line)
            for listener in self.rsp_listeners:
                if listener.handle_rsp(line):
                    break

    def __process_sm_stderr(self):
        """read smartmeter stderr and print to logger"""
        self.sm_stderr_lines = self.__read_all_from_pipe(self.sm_proc.stderr, self.sm_stderr_lines[-1]).split('\n')
        rsp = self.sm_stderr_lines[:-1]
        self.sm_stderr_lines = self.sm_stderr_lines[-1:]
        for line in rsp:
            self.logger.log('sm err: %s', line)

    def __process_sm_stdin(self):
        """write commands to smartmeter stdin"""
        processed_num_cmds = 0
        try:
            for i, cmd in enumerate(self.commands):
                cmd_len = len(cmd)
                written = os.write(self.sm_proc.stdin.fileno(), cmd)
                if written == cmd_len:
                    processed_num_cmds = processed_num_cmds + 1
                else:
                    self.commands[i] = self.commands[i][written:]
                    break
        except OSError, e:
            if e.errno != errno.EAGAIN:
                raise ProcError(str(self.bin_path) + ' write error: ' + str(e))
        finally:
            self.commands = self.commands[processed_num_cmds:]

    def start(self):
        if self.sm_proc is not None:
            raise UsageError('subprocess already running')
        self.terminate = False
        self.logger.log('starting subprocess %s ...', self.bin_path)
        self.sm_proc = subprocess.Popen([self.bin_path, '-p', self.device_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=4096, universal_newlines=True)
        self.logger.log('subprocess %s started', self.bin_path)
        self.__make_nonblock(self.sm_proc.stderr)
        self.__make_nonblock(self.sm_proc.stdout)
        self.__make_nonblock(self.sm_proc.stdin)
        self.sm_stdout_lines = ['']
        self.sm_stderr_lines = ['']
        self.sm_stderr_lines = ['']

    def run_once(self):
        if not self.terminate and self.sm_proc is not None:
            returncode = self.sm_proc.poll()
            if returncode is not None:
                # subprocess terminated
                self.sm_proc = None
                if not self.terminate:
                    self.terminate = True
                    raise ProcError(str(self.bin_path) + ' terminated with return code ' + str(returncode))
                return

            for g in self.cmd_generators:
                self.commands.extend(g.process())

            r, w, x = [], [], []
            r.append(self.sm_proc.stdout)
            r.append(self.sm_proc.stderr)
            if len(self.commands) > 0:
                w.append(self.sm_proc.stdin)

            next_timeout = 0.5
            r, w, x = select.select(r, w, x, next_timeout)
            if self.sm_proc.stdout in r:
                self.__process_sm_stdout()
            if self.sm_proc.stderr in r:
                self.__process_sm_stderr()
            if self.sm_proc.stdin in w:
                self.__process_sm_stdin()
            # TODO: fire timers

    def stop(self):
        self.terminate = True
        if self.sm_proc is not None:
            # DEBUG: remove this print
            self.logger.log('sm: %s', self.sm_stdout_lines[-1])
            if len(self.sm_stderr_lines[-1]) > 0:
                self.logger.log('sm err: %s', self.sm_stderr_lines[-1])

            self.logger.log('stopping subprocess %s ...', self.bin_path)
            os.kill(self.sm_proc.pid, signal.SIGTERM)
            self.sm_proc.wait()
            self.logger.log('subprocess %s stopped', self.bin_path)
            # FIXME: need a threadsafe way of stopping
            self.sm_proc = None
