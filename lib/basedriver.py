#!/usr/bin/env python3
"""
Base driver for em drivers
Implements common functionality
"""

import os
import re
import yaml

import emmgr.lib.config as config
import emmgr.lib.log as log
import emmgr.lib.util as util
import emmgr.lib.comm as comm

import jinja2

dummy = object()        # Used to differentiate between dummy and None


class ElementException(Exception):
    def __init__(self, msg, errno=1):
        self.msg = msg
        self.errno = errno


class BaseDriver:
    """
    Base class for all drivers
    """

    USERNAME_PASSWORD_INVALID = 2

    ElementException = ElementException

    def __init__(self,
                 hostname=None,
                 ipaddr_mgmt=None,
                 port=None,
                 model=None,
                 username=None,
                 password=None,
                 enable_password=None,
                 use_ssh=True,
                 definitions=None,
                 newline=None,
                 **kwargs                   # Ignore any additional parameters
                 ):
        self.hostname = hostname
        self.port = port
        self.ipaddr_mgmt = ipaddr_mgmt

        self.username = username
        self.password = password
        self.enable_password = enable_password
        self.use_ssh = use_ssh    # If true use ssh instead of telnet
        self.kwargs = kwargs
        self.newline = newline

        if self.ipaddr_mgmt:
            self.hostname = self.ipaddr_mgmt

        # ----
        self.transport = None
        self.em = None
        self.running_config = None
        
        if definitions == None:
            self._definitions = self.load_definitions(self.model)
        else:
            self._definitions = definitions

        self._wait_for_prompt = self.get_definition("config.wait_for_prompt", None)    # cache for performance

        if self.use_ssh:
            self.method = "ssh"
        else:
            self.method="telnet"
        self.transport = comm.RemoteConnection(timeout=10, method=self.method, newline=self.newline)
       
    @classmethod
    def load_definitions(cls, model=None):
        """
        Load definitions for the element
        This can be done recursively, for example a specific model can point to a generic one
        """
        definitions = []
        loaded_models = {}      # Track loaded models so we dont load each more than once
        while True:
            def_file = "%s/%s/%s-def.yaml" % (config.driver_dir, model, model)
            try:
                loaded_models[model] = True
                data = util.yaml_load(def_file)
                definitions.append(data)
                if 'driver' not in data:
                    break
                model = os.path.dirname(data.driver)
                if model in loaded_models:
                    break
            except yaml.YAMLError as err:
                raise self.ElementException("Cannot load element configuration %s, err: %s" % (def_file, err))
        return definitions

    def get_definition(self, attr, default=dummy):
        """
        Walk through each yaml file until we find the specified attribute
        Attributes can be specified hierarchically with dot as separator
        """
        if self._definitions is not None:
            attr = attr.split(".")
            for f in self._definitions:
                try:
                    for a in attr:
                        f = getattr(f, a)
                    return f
                except (KeyError, AttributeError):
                    pass
        if default is not dummy:
            return default
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

    @classmethod
    def get_models(cls):
        raise self.ElementException("Not implemented")
        
    def connect(self):
        log.debug("------------------- connect(%s, use_ssh=%s) -------------------" % (self.hostname, self.use_ssh))
        try:
            self.transport.connect(self.hostname, port=self.port, username=self.username, password=self.password)
        except comm.CommException as err:
            raise self.ElementException(err)
        self.em = comm.Expect(self.transport)

    def disconnect(self):
        raise self.ElementException("Not implemented")

    def reload(self, save_config=True):
        raise self.ElementException("Not implemented")

    def run(self, cmd=None, filter_=None, callback=None):
        raise self.ElementException("Not implemented")


    # ########################################################################
    # License
    # ########################################################################
    
    def license_get(self):
        raise self.ElementException("Not implemented")

    def license_set(self, url=None, save_config=True, reload=None, callback=None):
        raise self.ElementException("Not implemented")


    # ########################################################################
    # Configuration
    # ########################################################################

    def wait_for_prompt(self):
        log.debug("------------------- wait_for_prompt(%s) -------------------" % self.hostname)
        if not self._wait_for_prompt:
            raise self.ElementException("Not implemented")
        match = self.em.expect(self._wait_for_prompt)
        return match

    def configure(self, config_lines=None, save_running_config=False):
        raise self.ElementException("Not implemented")

    def enable_ssh(self):
        raise self.ElementException("Not implemented")

    def get_running_config(self, filter_=None, refresh=False, callback=None):
        """
        Fetch the running configuration, returns as a list of lines
        """
        raise self.ElementException("Not implemented")

    def save_running_config(self, callback=None):
        """
        Save running configuration as startup configuration
        """
        raise self.ElementException("Not implemented")

    def set_startup_config(self, config_lines=None, callback=None):
        """
        Set the startup_configuration to config_lines (list)
        """
        raise self.ElementException("Not implemented")

    # ########################################################################
    # Interface management
    # ########################################################################

    def interface_clear_config(self, interface=None, save_running_config=False, callback=None):
        """
        Default driver that resets a interface to its default configuration
        This default driver is used if there is a CLI command for this defined, 
        and method isn't overridden
        """
        try:
            cmd_template = self.get_definition("config.interface.clear_config.cmd")
        except KeyError:
            raise self.ElementException("Not implemented")
        t = jinja2.Template(cmd_template)
        cmd = t.render(interface_name=interface)
        cmd = cmd.split('\n')
        return self.configure(config_lines=cmd, save_running_config=save_running_config, callback=callback)

    def interface_get_admin_state(self, interface=None):
        """
        Default driver that retrieves an interface admin state
        This default driver is used if there is a CLI command for this.
        """
        raise self.ElementException("Not implemented")
        
    def interface_set_admin_state(self, interface=None, state=None, save_running_config=False, callback=None):
        """
        Default driver that enables/disables a interface
        This default driver is used if there is a CLI command for this defined, 
        and method isn't overridden
        """
        if state:
            attr = "config.interface.enable.cmd"
        else:
            attr = "config.interface.disable.cmd"
        try:
            cmd_template = self.get_definition(attr)
        except KeyError:
            raise self.ElementException("Not implemented")
        t = jinja2.Template(cmd_template)
        cmd = t.render(interface_name=interface)
        cmd = cmd.split('\n')
        return self.configure(config_lines=cmd, save_running_config=save_running_config, callback=callback)
    
        
    # ########################################################################
    # Topology
    # ########################################################################

    def l2_peers(self, interface=None, default_domain=None):
        """
        Returns the device L2 neighbours, using CDP, LLDP and similar protocols
        """
        raise self.ElementException("Not implemented")

    # ########################################################################
    # VLAN management
    # ########################################################################

    def vlan_get(self):
        """
        List all VLANs in the element
        Returns a dict, key is vlan ID
        """
        raise self.ElementException("Not implemented")
    
    def vlan_create(self, vlan=None, name=None):
        """
        Create a VLAN in the element
        """
        raise self.ElementException("Not implemented")
    
    def vlan_delete(self, vlan=None):
        """
        Delete a VLAN in the element
        """
        raise self.ElementException("Not implemented")
    
    def vlan_interface_get(self, interface=None):
        """
        Get all VLANs on an interface
        Returns a dict, key is vlan ID
        """
        raise self.ElementException("Not implemented")
    
    def vlan_interface_create(self, interface=None, vlan=None, tagged=True):
        """
        Create a VLAN on an interface
        """
        raise self.ElementException("Not implemented")
    
    def vlan_interface_delete(self, interface=None, vlan=None):
        """
        Delete a VLAN from an interface
        """
        raise self.ElementException("Not implemented")
    
    def vlan_interface_set_native(self, interface=None, vlan=None):
        """
        Set native VLAN on an Interface
        """
        raise self.ElementException("Not implemented")
     
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
        raise self.ElementException("Not implemented")

    def file_copy_to(self, mgr=None, filename=None, dest_filename=None, callback=None):
        """
        Copy file to element
        """
        raise self.ElementException("Not implemented")

    def file_copy_from(self, mgr=None, filename=None, callback=None):
        """
        Copy file from element
        """
        raise self.ElementException("Not implemented")

    def file_delete(self, filename, callback=None):
        """
        Delete file on element
        """
        raise self.ElementException("Not implemented")

    # ########################################################################
    # Software management
    # ########################################################################
    
    def sw_get_version(self):
        """
        Returns the version of the software running
        """
        raise self.ElementException("Not implemented")

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
        raise self.ElementException("Not implemented")

    def sw_copy_to(self, mgr=None, filename=None, dest_filename=None, callback=None):
        """
        Copy firmware to element
        """
        raise self.ElementException("Not implemented")

    def sw_copy_from(self, mgr=None, filename=None, callback=None):
        """
        Copy firmware from element
        """
        raise self.ElementException("Not implemented")

    def sw_delete(self, filename, callback=None):
        """
        Delete firmware from element
        """
        raise self.ElementException("Not implemented")

    def sw_delete_unneeded(self, callback=None):
        """
        Delete unneeded firmware from element
        """
        raise self.ElementException("Not implemented")

    def sw_set_boot(self, filename, callback=None):
        """
        Set which firmware to boot
        """
        raise self.ElementException("Not implemented")

    def sw_upgrade(self, mgr=None, filename=None, setboot=True, callback=None):
        """       
        Upgrade element firmware to filename
        If needed, other firmware is deleted to make room for the new firmware
        """
        raise self.ElementException("Not implemented")

    
    def get_bootloader(self, callback=None):
        """       
        Returns current bootloader
        """
        raise self.ElementException("Not implemented")

    def set_bootloader(self, mgr=None, filename=None, callback=None):
        """
        Copies bootloader to element and activates it
        """
        raise self.ElementException("Not implemented")
