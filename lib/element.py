#!/usr/bin/env python3
"""
Manage elemnts

This is a generic class, which gives a common API to elements.

Each element uses a driver, which does most of the work.
"""

import os
import sys
import yaml
import socket
from orderedattrdict import AttrDict

import emmgr.lib.config as config
import emmgr.lib.log as log
import emmgr.lib.util as util
import emmgr.lib.comm as comm


driverDir   = "/opt/emmgr/driver"   # todo, config


class ElementException(Exception):
    pass


class Element:
    """
    Manage one element
    """

    @classmethod
    def get_models(cls):
        res = []
        models = os.listdir(driverDir)
        models = sorted(models)
        for model in models:
            if model[0] != "_" and os.path.isdir(driverDir + os.sep + model):
                res.append(model)
        return res
        
    def __init__(self, hostname=None, ipaddr_mgmt=None, model=None):
        self.hostname    = hostname
        self.ipaddr_mgmt = ipaddr_mgmt
        self.model       = model

        if self.model is None:
            raise ElementException("Element model must be specified")
        
        # Load defaults from element config file
        def_file = "%s/%s/%s-def.yaml" % (driverDir, model, model)
        try:
            self.default_data = util.yaml_load(def_file)
        except yaml.YAMLError as err:
            raise ElementException("Cannot load element configuration %s, err: %s" % (def_file, err))

        if self.ipaddr_mgmt is None:
            # Find out management IP address through DNS
            addr = socket.gethostbyname(self.hostname)
            self.ipaddr_mgmt = addr
                
        # load the element driver for the element model
        driver_file = driverDir + "/%s.py" % self.default_data.driver
        if not os.path.exists(driver_file):
            raise ElementException("Missing element driver %s" % driver_file)
        self._drivermodule = util.import_file(driver_file)

        driver_args = config.em.scriptaccount
        driver_args.hostname = self.ipaddr_mgmt
        
        # Create instance of driver
        self._driver = self._drivermodule.Driver(**driver_args)


    # ########################################################################
    # Generic
    # ########################################################################

    def configure(self, config_lines=None, save_running_config=False):
        if not isinstance(config_lines, list):
            config_lines = [config_lines]
        return self._driver.configure(config_lines, save_running_config)

    def run(self, cmd=None, filter_=None, callback=None):
        return self._driver.run(cmd=cmd, filter_=filter_, callback=callback)

    def get_running_config(self, filter_=None, refresh=False, callback=None):
        return self._driver.get_running_config(filter_=filter_, refresh=refresh, callback=callback)

    def save_running_config(self, callback=None):
        return self._driver.save_running_config(callback=callback)

    def reload(self, save_config=True):
        self._driver.reload(save_config=save_config)

    # ########################################################################
    # Interface management
    # ########################################################################

    def interface_get_admin_state(self, interface):
        return self._driver.interface_get_admin_state(interface)

    def interface_set_admin_state(self, interface, enabled):
        self._driver.interface_set_admin_state(interface, enabled)

    def interface_clear_config(self, interface):
        self._driver.interface_clear_config(interface)

    # ########################################################################
    # VLAN management
    # ########################################################################

    def vlan_create(self, vlan, name):
        pass
    
    def vlan_delete(self, vlan):
        pass
    
    def vlan_interface_add(self, interface, vlan, tagged=False):
        pass
    
    def vlan_interface_delete(self, interface, vlan):
        pass
    
    def vlan_interface_set_native(self, interface, vlan):
        pass

     
    # ########################################################################
    # Software management
    # ########################################################################
    
    def sw_list(self, filter_=None, callback=None):
        if filter_ is None:
            filter_ = self.default_data.firmware_filter
        return self._driver.sw_list(filter_=filter_, callback=callback)

    def sw_copy_to(self, mgr=None, filename=None, dest_filename=None, callback=None):
        return self._driver.sw_copy_to(mgr=mgr, filename=filename, dest_filename=dest_filename, callback=callback)

    def sw_copy_from(self, mgr=None, filename=None, callback=None):
        return self._driver.sw_copy_from(mgr=mgr, filename=filename, callback=callback)

    def sw_delete(self, filename, callback=None):
        return self._driver.sw_delete(filename=filename, callback=callback)

    def sw_delete_unneeded(self, callback=None):
        return self._driver.sw_delete_unneeded(callback=callback)

    def sw_set_boot(self, filename, callback=None):
        return self._driver.sw_set_boot(filename, callback=callback)

    def sw_upgrade(self, mgr=None, filename=None, setboot=True, callback=None):
        return self._driver.sw_upgrade(mgr=mgr, filename=filename, setboot=setboot, callback=callback)


class BaseCLI(util.BaseCLI):
    
    def __init__(self):
        super().__init__()
        
        log.setLevel(self.args.loglevel)

        if self.args.hostname is None and self.args.ip is None:
            util.die("Error: You need to specify -H/--hostname or -i/--ip")
            
        if self.args.hostname != "__undefined__":
            self.em = Element(hostname=self.args.hostname, 
                              ipaddr_mgmt=self.args.ip, 
                              model=self.args.model)

    def add_arguments2(self):
        self.parser.add_argument('-H', '--hostname',
                                 help='Hostname of element')
        self.parser.add_argument('-i', '--ip',
                                 help='Management IP address of element')
        self.parser.add_argument('-m', '--model',
                                 required=True,
                                 help='Element model')
        self.parser.add_argument('-t',
                                 '--telnet',
                                 action='store_true',
                                 help='Use Telnet',
                                 default=False)
        self.parser.add_argument('--loglevel',
                                 choices=['info', 'warning', 'error', 'debug'],
                                 help='Set loglevel, one of < info | warning | error | debug >', 
                                 default='info' )

    def add_arguments(self):
        """Superclass overrides this to add additional arguments"""

    def run(self):
        raise ValueError("You must override the run() method")


class CLI_list_models(BaseCLI):
    
    def add_arguments(self):
        sys.argv += ["-H", "__undefined__", "-m", "none"]
        
    def run(self):
        print("Models:")
        for model in Element.get_models():
            print("   ", model)


class CLI_configure(BaseCLI):
    
    def add_arguments(self):
        self.parser.add_argument('-c', '--config',
                                 action="append",
                                 required=True,
                                 help='New configuration',
                                 )

    def run(self):
        print(self.args.config)
        res =  self.em.configure(config_lines=self.args.config)
        print("Result :", res)


class CLI_run(BaseCLI):
    
    def add_arguments(self):
        self.parser.add_argument('-c', '--command',
                                 required=True,
                                 help='Command to run',
                                 )

    def run(self):
        lines =  self.em.run(cmd=self.args.command)
        if lines:
            for line in lines:
                print(line)
        else:
            print("No output")


class CLI_get_running_config(BaseCLI):

    def run(self):
        lines = self.em.get_running_config()
        print("Running configuration:")
        if lines:
            for line in lines:
                print(line)
        else:
            print("No output")


class CLI_save_running_config(BaseCLI):

    def run(self):
        res = self.em.save_running_config()
        print("Result :", res)


class CLI_reload(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("-s", "--save_config",
                                 action="store_true",
                                 help='Save current config to startup config',
                                 default=False)

    def run(self):
        res = self.em.reload(save_config=self.args.save_config)
        print("Result :", res)


class CLI_interface_clear_config(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("--interface",
                                 help='Interface to clear',
                                 )

    def run(self):
        res = self.em.interface_clear_config(interface=self.args.interface)
        print("Result :", res)


class CLI_sw_exist(BaseCLI):
    def add_arguments(self):
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )

    def run(self):
        res = self.em.sw_exist(self.args.filename)
        print("Does firmware %s exist ? " % self.args.filename, res)


class CLI_sw_list(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument('--filter',
                                 help='Filter out firmware names',
                                 default=None)

    def run(self):
        sw_list = self.em.sw_list(filter_=self.args.filter)
        print("Softare on element:")
        for sw in sw_list:
            print("   ", sw)


class CLI_sw_copy_to(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )
        self.parser.add_argument('--server',
                                 default=config.em.default_firmware_server,
                                 help='Server to copy from/to',
                                 )
        self.parser.add_argument('--dest_filename',
                                 required=True,
                                 help='Destination filename',
                                 )

    def run(self):
        res = self.em.sw_copy_to(mgr=self.args.server,
                                 filename=self.args.filename,
                                 dest_filename=self.args.dest_filename,
                                 callback=self.callback,
                                 )
        print(res)

    def callback(self, status):
        print("   ", status)


# class CLI_sw_copy_from(BaseCLI):


class CLI_sw_set_boot(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )

    def run(self):
        try:
            res = self.em.sw_set_boot(self.args.filename)
            print("Set firmware to boot:", res)
        except comm.CommException as e:
            print("Error, %s" % (e.message))


class CLI_sw_delete(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )
    def run(self):
        try:
            res = self.em.sw_delete(self.args.filename)
            print("File deleted:", res)
        except comm.CommException as e:
            print("Error, %s" % (e.message))


class CLI_sw_delete_unneeded(BaseCLI):

    def run(self):
        try:
            deleted = self.em.sw_delete_unneeded()
            print("Files deleted: ", deleted)
        except comm.CommException as e:
            print("Error, %s" % (e.message))


class CLI_sw_upgrade(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )
        self.parser.add_argument('--server',
                                 default=config.em.default_firmware_server,
                                 help='Server to copy file from',
                                 )

    def run(self):
        if self.args.filename is None:
            raise comm.CommException(1, "Must specify filename")
        res = self.em.sw_upgrade(mgr=self.args.server,
                                 filename=self.args.filename,
                                 callback=self.callback,
                                 )
        print("sw_upgrade status:", res)

    def callback(self, status):
        print("   ", status)


def main():
    util.MyCLI(__name__)


if __name__ == '__main__':
    main()
