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

from emmgr.lib.basedriver import BaseDriver
import emmgr.lib.config as config
import emmgr.lib.log as log
import emmgr.lib.util as util
import emmgr.lib.comm as comm


driverDir   = "/opt/emmgr/driver"   # todo, config


class Element:
    """
    Manage one element. This is a stub that loads the real driver
    """

    ElementException = BaseDriver.ElementException  # for easy access

    @classmethod
    def get_models(cls):
        res = []
        models = os.listdir(driverDir)
        models = sorted(models)
        for model in models:
            if model[0] != "_" and os.path.isdir(driverDir + os.sep + model):
                res.append(model)
        return res

    def __init__(self, hostname=None, ipaddr_mgmt=None, model=None, use_ssh=None):
        self.hostname    = hostname
        self.ipaddr_mgmt = ipaddr_mgmt
        self.model       = model
        self.use_ssh     = use_ssh
        self._settings   = []           # List of settings, from yaml files
 
        if self.model is None:
            raise self.ElementException("Element model must be specified")
        
        if self.ipaddr_mgmt is None:
            # Find out management IP address through DNS
            addr = socket.gethostbyname(self.hostname)
            self.ipaddr_mgmt = addr

        self._load_settings()

        # load the element driver for the element model
        driver_file = driverDir + "/%s.py" % self._settings[-1].driver
        if not os.path.exists(driver_file):
            raise self.ElementException("Missing element driver %s" % driver_file)
        self._drivermodule = util.import_file(driver_file)

        driver_args = config.em.scriptaccount
        driver_args.hostname = self.ipaddr_mgmt
        driver_args.settings = self._settings
        if use_ssh is not None:
            driver_args.use_ssh = self.use_ssh
        
        # Create instance of driver
        self._driver = self._drivermodule.Driver(**driver_args)

    def _load_settings(self):
        """
        Load definitions for the element
        This can be done recursively, for example a specific model can point to a generic one
        """
        loaded_models = {}
        model = self.model
        # Load configuration for the element
        while True:
            def_file = "%s/%s/%s-def.yaml" % (driverDir, model, model)
            try:
                loaded_models[model] = 1
                data = util.yaml_load(def_file)
                self._settings.append(data)
                if 'driver' not in data:
                    return
                model = os.path.dirname(data.driver)
                if model in loaded_models:
                    return
            except yaml.YAMLError as err:
                raise self.ElementException("Cannot load element configuration %s, err: %s" % (def_file, err))

    def __getattr__(self, attr):
        """Bridge to the driver specific code"""
        return getattr(self._driver, attr)


# ########################################################################
#   CLI
# ########################################################################

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
        print("config", self.args.config)
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
        print(res)


# ########################################################################
# Topology
# ########################################################################

class CLI_l2_peers(BaseCLI):

    def run(self):
        peers = self.em.l2_peers()
        f="%-25s %-20s %-20s %s"
        print(f % ("Hostname", "Local iterface", "remote interface", "remote platform"))
        print(f % ("--------------", "--------------", "----------------", "---------------------"))
        for peer in peers:
            print(f % (peer.hostname, peer.local_if, peer.remote_if, peer.remote_platform))

# ########################################################################
# VLAN management
# ########################################################################


class CLI_vlan_get(BaseCLI):

    def run(self):
        """
        List all VLANs in the element
        Returns a dict, key is vlan ID
        """
        vlans = self.em.vlan_get()
        for vlan in vlans.values():
            print("    %5d  %s" % (vlan.id, vlan.name))
    

class CLI_vlan_create(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("-v", "--vlan",
                                 type=int,
                                 )
        self.parser.add_argument("-n", "--name",
                                 default=None
                                 )
    def run(self):
        """
        Create a VLAN in the element
        """
        res = self.em.vlan_create(vlan=self.args.vlan,
                                   name=self.args.name)
        print("res", res)
    
class CLI_vlan_delete(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("-v", "--vlan",
                                 type=int,
                                 )

    def run(self):
        """
        Delete a VLAN in the element
        """
        res = self.em.vlan_delete(vlan=self.args.vlan)
        print("res", res)
    

class CLI_vlan_interface_get(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("--interface")

    def run(self):
        """
        Get all VLANs on an interface
        Returns a dict, key is vlan ID
        """
        vlans = self.em.vlan_interface_get(interface=self.args.interface)
        for vlan in vlans.values():
             print("    %5d  %s" % (vlan.id, vlan.tagged))
        
class CLI_vlan_interface_create(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("--interface")
        self.parser.add_argument("-v", "--vlan",
                                 type=int,
                                 )
        self.parser.add_argument("--tagged",
                                 action="store_false",
                                 default=True,
                                 )

    def run(self):
        """
        Create a VLAN to an interface
        """
        res = self.em.vlan_interface_create(interface=self.args.interface, 
                                             vlan=self.args.vlan,
                                             tagged=self.args.tagged)
        print("res", res)                                        
    
class CLI_vlan_interface_delete(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("--interface")
        self.parser.add_argument("--vlan",
                                 type=int,
                                 )
    def run(self):
        """
        Delete a VLAN from an interface
        """
        res = self.em.vlan_interface_delete(interface=self.args.interface, 
                                            vlan=self.args.vlan)
        print("res", res)                                        
    
class CLI_vlan_interface_set_native(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("-i", "--interface")
        self.parser.add_argument("-v", "--vlan",
                                 type=int,
                                 )

    def run(self):
        """
        Set native VLAN on an Interface
        """
        raise ElementException("Not implemented")

# ########################################################################
# Software management
# ########################################################################
    
class CLI_sw_list(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument('--filter',
                                 help='Filter out firmware names',
                                 default=None)

    def run(self):
        sw_list = self.em.sw_list(filter_=self.args.filter)
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


class CLI_license_set(BaseCLI):
    
    def add_arguments(self):
        self.parser.add_argument('--url',
                                 required=True,
                                 help='URL to license file storage',
                                 )
        self.parser.add_argument('--reload',
                                 default=False,
                                 action="store_true",
                                 help='Reload when license is installed',
                                 )

    def run(self):
        
        try:
            res =  self.em.license_set(url=self.args.url, reload=self.args.reload)
            print("Result :", res)
        except self.em.ElementException as err:
            print(err)


def main():
    util.MyCLI(__name__)


if __name__ == '__main__':
    main()
