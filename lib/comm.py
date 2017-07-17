#!/usr/bin/env python3
'''
Functionality to communicate with remote nodes, in a Expect like way

Supports ssh and telnet
'''

import os.path
import re
import select
import pty

import emmgr.lib.log as log


class CommException(Exception):
    def __init__(self, errno, message):
        self.errno = errno
        self.message = message


class RemoteConnection:
    """
    Run telnet or ssh, with an API compatible with Telnet()
    This class handles the decode/encode from/to string and bytes
    """

    def __init__(self, codec="ascii", timeout=60, method=None, newline="\n"):
        self._codec = codec
        self._timeout = timeout
        self._method = method

        self._buffer = b""
        self.status = ""
        self.newline = newline

    def connect(self, host, username):
        if self._method == "ssh":
            cmd = ["/usr/bin/ssh",
                   "-l", username,
                   "-o", "UserKnownHostsFile=/dev/null",
                   "-o", "StrictHostKeyChecking=no",
                   str(host)]
        elif self._method == "telnet":
            cmd = ["telnet", "-e", "^A", str(host)]
        else:
            raise CommException(1, "Unknown connection method %s" % self.method)

        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.execvp(cmd[0], cmd)  # replace process
            os._exit(1)             # fail to execv
        if self._method == "telnet":
            # os.write(self.fd, bytearray([255, 254, 1])) # IAC DONT ECHO
            # force character at a time
            pass
            os.write(self.fd, b"\001")
            os.write(self.fd, b"mode character\n")
            os.write(self.fd, b"\001")
            os.write(self.fd, b"send dont echo\n")
            # time.sleep(0.5)
            # fcntl.fcntl(self.fd, fcntl.F_SETFL, os.O_NONBLOCK)
        return True

    def disconnect(self):
        os.close(self.fd)

    def unread(self, data):
        """
        Return data to beginning of buffer
        """
        self._buffer = data.encode(self._codec) + self._buffer

    def read(self, length=2000000, timeout=None):
        """
        read from subprocess
        If length==None, wait for newline, otherwise read length bytes
        """

        if length is None:
            if b"\r\n" in self._buffer:
                data, tmp, self._buffer = self._buffer.partition(b"\r\n")
                return data.decode(self._codec)

        while True:
            read_sockets, write_sockets, error_sockets = \
                select.select([self.fd], [], [], self._timeout)
            if read_sockets == []:
                # timeout
                return None

            for sock in read_sockets:
                # if sock == self.p.stdout:
                if sock == self.fd:
                    try:
                        if length:
                            # data = sock.read(length)
                            data = os.read(sock, length)
                        else:
                            # data = sock.read(4096)
                            data = os.read(sock, 4096)
                        if data == "":
                            return None  # disconnected
                    except OSError:
                        return None  # disconnect
                    # sys.stdout.flush()
                    self._buffer += data
                    if length is None:
                        if b"\r\n" in self._buffer:
                            data, tmp, self._buffer = self._buffer.partition(b"\r\n")
                            return data.decode(self._codec)
                    else:
                        if len(self._buffer) >= length:
                            data = self._buffer[:length].decode(self._codec)
                            self._buffer = self._buffer[length:]
                            return data
                else:
                    log.error("Unknown socket %s during read()" % (sock))

    def readline(self, timeout=None):
        """
        read from subprocess until newline received
        """
        raise CommException("Not implemented")

    def write(self, line):
        """
        Write to subprocess
        We use select so we don't overrun/block the subprocess
        """
        line = line.encode(self._codec)
        while True:
            read_sockets, write_sockets, error_sockets = \
                select.select([], [self.fd], [], self._timeout)
            # select.select([], [self.p.stdin], [], self._timeout)

            if write_sockets == []:
                log.error("write() timeout")
                # timeout
                return None

            for sock in write_sockets:
                # if sock == self.p.stdin:
                if sock == self.fd:
                    try:
                        if len(line) < 512:
                            os.write(sock, line)
                            return
                        os.write(sock, line[:512])
                        line = line[512:]
                    except OSError:
                        return None
                else:
                    log.error("Unknown socket %s during write()" % (sock))

    def writeln(self, msg):
        self.write(msg)
        self.write(self.newline)

    def flush(self):
        # self.p.stdin.flush()
        # self.output.flush()
        pass


class Expect:
    """
    Implements expect functionality, to easily work with network elements
    Need a transport instance that does the actual communication
    An instance of RemoteConnection is a good candidates
    """

    def __init__(self, transport=None):
        self.transport = transport
        self.before = ''
        self.match = None        # result from last match
        self.buffer = ""
        self.prev_data = ""

    def _get(self, timeout=None):
        if self.prev_data:
            tmp = self.prev_data
            self.prev_data = ""
            return tmp
        return self.transport.read(4096, timeout)

    def expect(self, matches, timeout=20):
        """
        Wait until match or timeout
        If match, returns key of which regex matched
        if no match (timeout), returns None
        """
        self.before = ''
        self.match = None

        if isinstance(matches, str):
            matches = {'0': matches}

        elif isinstance(matches, list):
            tmp = {}
            ix = 0
            for match in matches:
                tmp[ix] = match
                ix += 1
            matches = tmp

        regexes = {}
        for key, match in matches.items():
            regexes[key] = re.compile(match)

        log.debug("expect, match criteria %s" % regexes)
        while True:
            c = self.transport.read(1, timeout)
            # c = self._get(timeout)
            if c is None:
                break
            self.before += c
            for key, regex in regexes.items():
                m = regex.search(self.before)
                if m:
                    # self.prev_data = self.before[m.end():]  # save everything after our match
                    self.match = m.group()
                    log.debug("  expect, matched: %s" % self.match)
                    tmp = self.before.replace("\n", "\\n")
                    tmp = tmp.replace("\r", "\\r")
                    log.debug("  expect, self.before: %s" % tmp)
                    return key
        raise CommException(1, "  expect, timeout, self.before: %s" % self.before)

    def read(self, maxlen):
        return self.transport.read(maxlen)

    def write(self, msg):
        log.debug("expect write: %s" % msg)
        self.transport.write(msg)

    def writeln(self, msg):
        log.debug("expect writeln: %s" % msg)
        self.transport.writeln(msg)


def main():
    pass


if __name__ == "__main__":
    main()
