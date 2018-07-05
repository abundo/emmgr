"""
Base driver for em drivers
Implements common functionality
"""

import re

class ElementException(Exception):
    pass


class BaseDriver:

    ElementException = ElementException

    def __init__(self, hostname=None,
                 port=None,
                 username=None,
                 password=None,
                 enable_password=None,
                 use_ssh=True,
                 settings=None,
                 ):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.enable_password = enable_password
        self.use_ssh = use_ssh    # If true use ssh instead of telnet
        self.settings = settings

        self.transport = None
        self.em = None
        self.running_config = None


    def s(self, attr, default=None):
        """
        Walk through each yaml file until we find the attribute
        """
        for f in self.settings:
            try:
                if hasattr(f, attr):
                    return getattr(f, attr)
            except KeyError:
                print("KeyError")
                pass
        raise KeyError("Unknown attribute %s" % attr)


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

    def str_to_lines(self, lines):
        if isinstance(lines, str):
            lines = lines.split("\n")
        if not isinstance(lines, list):
            lines = [lines]
        return lines

    # ########################################################################
    # Generic
    # ########################################################################

    def connect(self):
        raise ElementException("Not implemented")

    def disconnect(self):
        raise ElementException("Not implemented")

    def reload(self, save_config=True):
        raise ElementException("Not implemented")

    def license_set(self, url=None, save_config=True, reload=None, callback=None):
        raise ElementException("Not implemented")

    def run(self, cmd=None, filter_=None, callback=None):
        raise ElementException("Not implemented")

    # ########################################################################
    # Configuration
    # ########################################################################

    def wait_for_prompt(self):
        # todo, wait for should be in config file
        log.debug("------------------- wait_for_prompt() -------------------")
        match = self.em.expect("#")
        return match

    def configure(self, config_lines=None, save_running_config=False):
        raise ElementException("Not implemented")

    def enable_ssh(self):
        raise ElementException("Not implemented")

    def get_running_config(self, filter_=None, refresh=False, callback=None):
        """
        Fetch the running configuration, returns as a list of lines
        """
        raise ElementException("Not implemented")

    def save_running_config(self, callback=None):
        """
        Save running configuration as startup configuration
        """
        raise ElementException("Not implemented")

    def set_boot_config(self, config_lines=None, callback=None):
        """
        Set the startup_configuration to config_lines (list)
        """
        raise ElementException("Not implemented")

    # ########################################################################
    # Interface management
    # ########################################################################

    def interface_clear_config(self, interface):
        """
        Default driver that resets a interface to its default configuration
        This default driver is used if there is a CLI command for this.
        """
        raise ElementException("Not implemented")

    def interface_get_admin_state(self, interface, enabled):
        """
        Default driver that enables/disables a interface
        This default driver is used if there is a CLI command for this.
        """
        raise ElementException("Not implemented")
        
    def interface_set_admin_state(self, interface, enabled):
        """
        Default driver that enables/disables a interface
        This default driver is used if there is a CLI command for this.
        """
        raise ElementException("Not implemented")
        
    # ########################################################################
    # Topology
    # ########################################################################

    def l2_peers(self):
        """
        Returns the device L2 neighbours, using CDP, LLDP and similar protocols
        """
        raise ElementException("Not implemented")

    # ########################################################################
    # VLAN management
    # ########################################################################

    def vlan_get(self):
        """
        List all VLANs in the element
        Returns a dict, key is vlan ID
        """
        raise ElementException("Not implemented")
    
    def vlan_create(self, vlan=None, name=None):
        """
        Create a VLAN in the element
        """
        raise ElementException("Not implemented")
    
    def vlan_delete(self, vlan=None):
        """
        Delete a VLAN in the element
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_get(self, interface=None):
        """
        Get all VLANs on an interface
        Returns a dict, key is vlan ID
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_create(self, interface=None, vlan=None, tagged=True):
        """
        Create a VLAN on an interface
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_delete(self, interface=None, vlan=None):
        """
        Delete a VLAN from an interface
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_set_native(self, interface=None, vlan=None):
        """
        Set native VLAN on an Interface
        """
        raise ElementException("Not implemented")
     
    # ########################################################################
    # File management
    # ########################################################################

    def file_exist(self, filename, callback=None):
        """
        Returns true if filename exist on element
        """
        file_list = self.file_list(callback=callback)
        return filename in file_list
    
    def file_list(self, filter_=None, callback=None):
        """
        List all files on the element
        """
        raise ElementException("Not implemented")

    def file_copy_to(self, mgr=None, filename=None, dest_filename=None, callback=None):
        """
        Copy file to element
        """
        raise ElementException("Not implemented")

    def file_copy_from(self, mgr=None, filename=None, callback=None):
        """
        Copy file from element
        """
        raise ElementException("Not implemented")

    def file_delete(self, filename, callback=None):
        """
        Delete file on element
        """
        raise ElementException("Not implemented")

    # ########################################################################
    # Software management
    # ########################################################################
    
    def sw_exist(self, filename, callback=None):
        """
        Returns true if filename exist on element
        """
        sw_list = self.sw_list(callback=callback)
        return filename in sw_list

    def sw_list(self, filter_=None, callback=None):
        """
        List all firmware on the element
        """
        raise ElementException("Not implemented")

    def sw_copy_to(self, mgr=None, filename=None, dest_filename=None, callback=None):
        """
        Copy firmware to element
        """
        raise ElementException("Not implemented")

    def sw_copy_from(self, mgr=None, filename=None, callback=None):
        """
        Copy firmware from element
        """
        raise ElementException("Not implemented")

    def sw_delete(self, filename, callback=None):
        """
        Delete firmware from element
        """
        raise ElementException("Not implemented")

    def sw_delete_unneeded(self, callback=None):
        """
        Delete unneeded firmware from element
        """
        raise ElementException("Not implemented")

    def sw_set_boot(self, filename, callback=None):
        """
        Set whihch firmware to boot
        """
        raise ElementException("Not implemented")

    def sw_upgrade(self, mgr=None, filename=None, setboot=True, callback=None):
        """       
        Upgrade element firmware to filename
        If needed, other firmware is deleted to make room for the new firmware
        """
        raise ElementException("Not implemented")
