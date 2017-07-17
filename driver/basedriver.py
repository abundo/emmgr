"""
Base driver for em drivers
Implements common functionality
"""

import re

class BaseDriver:

    def __init__(self, hostname=None, port=None, username=None, password=None, enable_password=None, use_ssh=True):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.enable_password = enable_password
        self.use_ssh = use_ssh    # If true use ssh instead of telnet

        self.transport = None
        self.em = None
        self.running_config = None

    def sw_exist(self, filename, callback=None):
        sw_list = self.sw_list(callback=callback)
        return filename in sw_list

    def filter_(self, lines, filter_):
        """
        Accept a list
        Returns a list, with matching lines according to filter_ (regex)
        """
        if filter_ is None:
            return lines
        match = []
        p = re.compile(filter_)
        for line in lines:
            if p.search(line):
                match.append(line)
        return match

    def interface_set_admin_state(self, interface, enabled):
        """
        Default driver that enables/disables a interface
        This default driver is used if there is a CLI command for this.
        """
        
    def interface_get_admin_state(self, interface, enabled):
        """
        Default driver that enables/disables a interface
        This default driver is used if there is a CLI command for this.
        """
        

    def interface_clear_config(self, interface):
        """
        Default driver that resets a interface to its default configuration
        This default driver is used if there is a CLI command for this.
        """
