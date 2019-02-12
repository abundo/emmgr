#!/usr/bin/env python3
'''
Functionality to communicate with remote nodes, in a Expect like way

Supports ssh and telnet
'''

import os.path
import re
import select
import telnetlib
import socket
import ssh2.session

import emmgr.lib.log as log


class CommException(Exception):
    def __init__(self, errno, message):
        self.errno = errno
        self.message = message


class Telnet_Connection:
    """
    A Wrapper for a telnet connection
    """
    def __init__(self, host, port=None, username=None, password=None, timeout=None):
        """
        Open a telnet connection
        """
        if port is None: 
            port = 23
        try:
            self.tn = telnetlib.Telnet(host=str(host), port=port, timeout=timeout)
        except socket.timeout as err:
            raise CommException(1, "Timeout connecting to %s" % host)
        self.fd = self.tn.fileno()
    
    def get_socket(self):
        return self.tn.get_socket()

    def read(self, length=None, timeout=None):
        return self.tn.read_eager()
    
    def write(self, data):
        self.tn.write(data)


class SSH_Connection:
    """
    A Wrapper for a SSH connection
    """
    def __init__(self, host, port=None, username=None, password=None, timeout=None):
        """
        Open a SSH connection and authenticate
        """
        if port is None:
            port = 22
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout:
            self.sock.settimeout(timeout)
        log.debug("------------------- socket.connect(%s) -------------------" % host)
        try:
            self.sock.connect((str(host), port))
        except (ConnectionRefusedError, OSError) as err:
            raise CommException(1, "socket.connect() host %s, err %s" % (host, err))

        self.ssh_session = ssh2.session.Session()
        if timeout:
            self.ssh_session.set_timeout(timeout * 1000)   # In milliseconds
        log.debug("------------------- ssh_session.handshake(%s) -------------------" % host)
        try:
            self.ssh_session.handshake(self.sock)
        except ssh2.exceptions.SocketRecvError as err:
            raise CommException(1, err)
        log.debug("------------------- ssh_session.userauth_password(%s) -------------------" % host)
        self.ssh_session.userauth_password(username, password)

        log.debug("------------------- ssh_session.open_session(%s) -------------------" % host)
        self.channel = self.ssh_session.open_session()
        log.debug("------------------- channel.pty(%s) -------------------" % host)
        self.channel.pty(term="vt100")
        # self.channel.pty(term="dumb")
        log.debug("------------------- channel.shell(%s) -------------------" % host)
        self.channel.shell()
        self.fd = self.sock.fileno()

    def read(self, length=None, timeout=None):
        size, data = self.channel.read(size = length)
        return data
    
    def write(self, data):
        self.channel.write(data)
    
    def close(self):
        self.channel.close()
        self.sock.close()
        self.fd = -1


class RemoteConnection:
    """
    Open a telnet or ssh connection
    This class 
    - handles the decode/encode between string and bytes
    - ensures that all newlines follows unix style "\n"
    """

    def __init__(self, codec="utf8", timeout=60, method=None, newline="\n"):
        self._codec = codec
        self._timeout = timeout
        self._method = method

        self._buffer = b""
        self.status = ""
        self.newline = newline

    def connect(self, host, port=None, username=None, password=None):
        if self._method == "ssh":
            self.conn = SSH_Connection(host, port=port, username=username, password=password, timeout=self._timeout)

        elif self._method == "telnet":
            self.conn = Telnet_Connection(host, port=port, timeout=self._timeout)

        else:
            raise CommException(1, "Unknown connection method %s" % self.method)

    def disconnect(self):
        self.conn.close()

    def unread(self, data):
        """
        Return data to beginning of buffer
        """
        self._buffer = data.encode(self._codec) + self._buffer

    def read(self, length=4096, timeout=None):
        """
        read from connection
        length is maximum number of bytes to read
        """
        while True:
            # return data from buffer if we have any
            if length and len(self._buffer):
                if length < len(self._buffer):
                    data = self._buffer[:length]
                    self._buffer = self._buffer[length:]
                else:
                    data = self._buffer
                    self._buffer = b""
                return data.decode(self._codec)

            read_sockets, write_sockets, error_sockets = \
                select.select([self.conn.fd], [], [], self._timeout)
            if read_sockets == []:
                # timeout
                return None

            for sock in read_sockets:
                if sock == self.conn.fd:
                    try:
                        if length:
                            data = self.conn.read(length)
                        else:
                            data = self.conn.read()
                        if data == "":
                            return None  # disconnected
                    except OSError:
                        return None  # disconnect
                    self._buffer += data
                else:
                    log.error("Unknown socket %s during read()" % (sock))

    def readline(self, timeout=None):
        """
        read from connection until newline received
        """
        while True:
            if b"\r\n" in self._buffer:
                data, tmp, self._buffer = self._buffer.partition(b"\r\n")
                return data.decode(self._codec)

            read_sockets, write_sockets, error_sockets = \
                select.select([self.fd], [], [], self._timeout)
            if read_sockets == []:
                # timeout
                return None

            for sock in read_sockets:
                if sock == self.fd:
                    try:
                        data = os.read(sock, 4096)
                        if data == "":
                            return None  # disconnected
                    except OSError:
                        return None  # disconnect
                    self._buffer += data
                else:
                    raise CommException("Unknown socket %s during read()" % (sock))

    def write(self, line):
        """
        Write to connection
        We use select so we don't overrun/block the connection
        """
        line = line.encode(self._codec)
        while True:
            read_sockets, write_sockets, error_sockets = \
                select.select([], [self.conn.fd], [], self._timeout)

            if write_sockets == []:
                log.error("write() timeout")
                # timeout
                return None

            for sock in write_sockets:
                # if sock == self.p.stdin:
                if sock == self.conn.fd:
                    try:
                        if len(line) < 512:
                            self.conn.write(line)
                            return
                        self.conn.write(line[:512])
                        line = line[512:]
                    except OSError:
                        return None
                else:
                    raise CommException("Unknown socket %s during write()" % (sock))

    def writeln(self, msg=None):
        if msg:
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
            c = self.transport.read(timeout=timeout)
            if c is None:
                break
            self.before += c
            for key, regex in regexes.items():
                m = regex.search(self.before)
                if m:
                    self.match = m.group()
                    log.debug("  expect, matched: %s" % self.match)

                    tmp = self.before[:m.end()]    # Everthing up to matched text
                    tmp = tmp.replace("\n", "\\n")
                    tmp = tmp.replace("\r", "\\r")
                    log.debug("  expect, self.before: %s" % tmp)
                    log.debug("  expect, returned to buffer: '%s'" % self.before[m.end():])
                    self.transport.unread(self.before[m.end():])  # text after match is returned to transport
                    return key
        raise CommException(1, "  expect, timeout, self.before: %s" % self.before)

    def read(self, maxlen):
        return self.transport.read(maxlen)

    def write(self, msg):
        log.debug("expect write: %s" % msg)
        self.transport.write(msg)

    def writeln(self, msg=None):
        log.debug("expect writeln: '%s'" % msg)
        self.transport.writeln(msg)


def main():
    pass


if __name__ == "__main__":
    main()
