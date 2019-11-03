#!/usr/bin/env python3
'''
Common CLI for classes and drivers
'''

import sys
import re

import emmgr.lib.config as config
import emmgr.lib.log as log
import emmgr.lib.util as util
import emmgr.lib.comm as comm

hostconfig = config.em.scriptaccount


class BaseCLI(util.BaseCLI):
    """
    Common parametrars for all CLI classes
    """
    
    def __init__(self, **kwargs):
        self.mgr_cls = kwargs.pop("mgr_cls")
        super().__init__(**kwargs)
        

    def add_arguments(self):
        self.parser.add_argument('-H', '--hostname',
                                 help='Hostname of element')
        self.parser.add_argument('-i', '--ipaddr_mgmt',
                                 help='Management IP address of element')
        self.parser.add_argument('-m', '--model',
                                 required=True,
                                 help='Element model')
        self.parser.add_argument('-u', '--username',
                                 default=hostconfig['username'],
                                 help='Username for connecting',)
        self.parser.add_argument('-p', '--password',
                                 default=hostconfig['password'],
                                 help='Password for connecting',)
        self.parser.add_argument('-e', '--enable_password',
                                 default=hostconfig['enable_password'],
                                 help='Password for enable mode',)
        self.parser.add_argument('-t', '--telnet',
                                 action='store_false',
                                 help='Use Telnet',
                                 dest='use_ssh',
                                 default=True)
        self.parser.add_argument('--loglevel',
                                 choices=['info', 'warning', 'error', 'debug'],
                                 help='Set loglevel, one of info, warning, error or debug',
                                 default='info' )

    def run(self):
        if self.args.hostname is None and self.args.ipaddr_mgmt is None:
            util.die('Error: You need to specify -H/--hostname or -i/--ipaddr_mgmt')

        log.setLevel(self.args.loglevel)
        self.mgr = self.mgr_cls(**vars(self.args))


# ########################################################################
# Generic
# ########################################################################

class CLI_list_models(BaseCLI):
    
    def add_arguments(self):
        """Avoid adding default arguments"""
        pass
    
    def run(self):
        print("Models:")
        for model in self.mgr_cls.get_models():
            print("   ", model)
 
 
class CLI_reload(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("-s", "--save_config",
                                 action="store_true",
                                 help='Save current config to startup config',
                                 default=False)

    def run(self):
        try:
            super().run()
            res = self.mgr.reload(save_config=self.args.save_config)
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_run(BaseCLI):
    
    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('-c', '--command',
                                 required=True,
                                 action="append",
                                 help='Command to run',
                                 )

    def run(self):
        try:
            super().run()
            for cmd in self.args.command:
                log.debug("cmd: %s" % cmd)
                lines = self.mgr.run(cmd=cmd)
                if lines:
                    ix = 0
                    for line in lines:
                        #print("%d %s" % (ix, line))
                        print("%s" % (line))
                        ix += 1
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


# ########################################################################
# Configuration
# ########################################################################

class CLI_configure(BaseCLI):
    
    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('-c', '--config',
                                 action="append",
                                 help='New configuration',
                                 )
        self.parser.add_argument('-f', '--file',
                                 help='File with configuration commands',
                                 )
        self.parser.add_argument('-s', '--save_running_config',
                                 default=False,
                                 action="store_true",
                                 help='File with configuration commands',
                                 )

    def run(self):
        if not (self.args.config or self.args.file):
            print("Error: You need to specify config or file")
            sys.exit(1)
        try:
            super().run()
            if self.args.file:
                lines = []
                for line in open(self.args.file):
                        lines.append(line.strip())
            else:
                lines = self.args.config
            res =  self.mgr.configure(config_lines=lines, save_running_config=self.args.save_running_config)
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_get_running_config(BaseCLI):

    def run(self):
        try:
            super().run()
            lines = self.mgr.get_running_config()
            print("Running configuration:")
            if lines:
                for line in lines:
                    print(line)
            else:
                print("No output")
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_save_running_config(BaseCLI):

    def run(self):
        try:
            super().run()
            res = self.mgr.save_running_config()
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_set_startup_config(BaseCLI):

    def run(self):
        try:
            super().run()
            print("Not implemented")
            #res = self.mgr.save_running_config()
            #print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)

# ########################################################################
# Interface management
# ########################################################################


class CLI_interface_clear_config(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("--interface",
                                 help='Interface to clear',
                                 )

    def run(self):
        try:
            super().run()
            res = self.mgr.interface_clear_config(interface=self.args.interface)
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_interface_get_admin_state(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("--interface",
                                 required=True,
                                 )

    def run(self):
        try:
            super().run()
            res = self.mgr.interface_get_admin_state(interface=self.args.interface)
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_interface_set_admin_state(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("--interface",
                                 help='Interface to modify',
                                 required=True,
                                 )
        self.parser.add_argument("-s", "--state",
                                 help='new state',
                                 required=True,
                                 type=util.str2bool,
                                 )

    def run(self):
        try:
            super().run()
            res = self.mgr.interface_set_admin_state(interface=self.args.interface,
                                                    state=self.args.state)
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


# ########################################################################
# Topology
# ########################################################################

class CLI_l2_peers(BaseCLI):

    def run(self):
        try:
            super().run()
            peers = self.mgr.l2_peers()
            for peer in peers:
                print("peer", peer)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


# ########################################################################
# VLAN management
# ########################################################################

class CLI_vlan_get(BaseCLI):

    def run(self):
        """
        List all VLANs in the element
        Returns a dict, key is vlan ID
        """
        try:
            super().run()
            vlans = self.mgr.vlan_get()
            for vlan in vlans.values():
                print("    %5d  %s" % (vlan.id, vlan.name))
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)
    

class CLI_vlan_create(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
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
        try:
            super().run()
            res = self.mgr.vlan_create(vlan=self.args.vlan,
                                    name=self.args.name)
            print("res", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)
    

class CLI_vlan_delete(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("-v", "--vlan",
                                 type=int,
                                 )

    def run(self):
        """
        Delete a VLAN in the element
        """
        try:
            super().run()
            res = self.mgr.vlan_delete(vlan=self.args.vlan)
            print("res", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)
    

class CLI_vlan_interface_get(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("--interface")

    def run(self):
        """
        Get all VLANs on an interface
        Returns a dict, key is vlan ID
        """
        try:
            super().run()
            vlans = self.mgr.vlan_interface_get(interface=self.args.interface)
            for id, tagged in vlans.items():
                print("    %5d  %s" % (id, tagged))
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)
        

class CLI_vlan_interface_create(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("--interface")
        self.parser.add_argument("-v", "--vlan",
                                 type=int,
                                 )
        self.parser.add_argument("--untagged",
                                 action="store_true",
                                 default=False,
                                 )

    def run(self):
        """
        Create a VLAN to an interface
        """
        try:
            super().run()
            res = self.mgr.vlan_interface_create(interface=self.args.interface, 
                                                vlan=self.args.vlan,
                                                untagged=self.args.untagged)
            print("res", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_vlan_interface_delete(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("--interface")
        self.parser.add_argument("--vlan",
                                 type=int,
                                 )
    def run(self):
        """
        Delete a VLAN from an interface
        """
        try:
            super().run()
            res = self.mgr.vlan_interface_delete(interface=self.args.interface, 
                                                vlan=self.args.vlan)
            print("res", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)
    

class CLI_vlan_interface_set_native(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument("-i", "--interface")
        self.parser.add_argument("-v", "--vlan",
                                 type=int,
                                 )

    def run(self):
        """
        Set native VLAN on an Interface
        """
        try:
            super().run()
            print("Error: Not implemented")
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


# ########################################################################
# Software management
# ########################################################################

class CLI_sw_get_version(BaseCLI):
#    def add_arguments(self):
#        super().add_arguments()

    def run(self):
        try:
            super().run()
            res = self.mgr.sw_get_version()
            print(res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)

class CLI_sw_exist(BaseCLI):
    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )

    def run(self):
        try:
            super().run()
            res = self.mgr.sw_exist(self.args.filename)
            print("Does firmware %s exist ? " % self.args.filename, res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_sw_get_boot(BaseCLI):

    def run(self):
        try:
            super().run()
            res = self.mgr.sw_get_boot()
            print("System will boot with firmware:", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_sw_list(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('--filter',
                            help='Filter out firmware names',
                            default=None)

    def run(self):
        try:
            super().run()
            sw_list = self.mgr.sw_list(filter_=self.args.filter)
            print("Softare on element:")
            for sw in sw_list:
                print("   ", sw)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)
    

class CLI_sw_copy_to(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )
        self.parser.add_argument('--server',
                                 default=config.em.default_firmware_server,
                                 help='Server to copy from/to',
                                 )
        self.parser.add_argument('--dest_filename',
                                 default=None,
                                 help='Destination filename',
                                 )

    def run(self):
        try:
            super().run()
            res = self.mgr.sw_copy_to(mgr=self.args.server, 
                                    filename=self.args.filename, 
                                    dest_filename=self.args.dest_filename,
                                    callback=self.callback,
                                    )
            print(res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)

    def callback(self, status):
        print("   ", status)


# class CLI_sw_copy_from(BaseCLI):


class CLI_sw_set_boot(BaseCLI):
        
    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )
    def run(self):
        try:
            super().run()
            res = self.mgr.sw_set_boot(self.args.filename)
            print("Set firmware to boot:", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_sw_delete(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )
    def run(self):
        try:
            super().run()
            res = self.mgr.sw_delete(self.args.filename)
            print("File deleted:", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_sw_delete_unneeded(BaseCLI):

    def run(self):
        try:
            super().run()
            deleted = self.mgr.sw_delete_unneeded()
            print("Files deleted: ", deleted)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_sw_upgrade(BaseCLI):
    
    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )
        self.parser.add_argument('--server',
                                 default=config.em.default_firmware_server,
                                 help='Server to copy from/to',
                                 )
    def run(self):
        try:
            super().run()
            if self.args.filename is None:
                raise self.ElementException("Must specify filename")
            res = self.mgr.sw_upgrade(mgr=self.args.server, 
                                    filename=self.args.filename,
                                    callback=self.callback,
                                    )
            print("sw_upgrade status:", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)

    def callback(self, status):
        print("   ", status)


class CLI_get_bootloader(BaseCLI):

    def run(self):
        try:
            super().run()
            bootloader = self.mgr.get_bootloader()
            print("Bootloader in use: '%s'" % bootloader)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_set_bootloader(BaseCLI):

    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('--server',
                                 default=config.em.default_firmware_server,
                                 help='Server to copy from/to',
                                 )
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )

    def run(self):
        try:
            super().run()
            res = self.mgr.set_bootloader(mgr=self.args.server, 
                                    filename=self.args.filename, 
                                    callback=self.callback,
                                    )
            print(res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)
        
    def callback(self, status):
        print("   ", status)


# ########################################################################
# License management
# ########################################################################

class CLI_license_get(BaseCLI):
    
    def run(self):
        try:
            super().run()
            res =  self.mgr.license_get()
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


class CLI_license_set(BaseCLI):
    
    def add_arguments(self):
        super().add_arguments()
        self.parser.add_argument('--url',
                                 required=True,
                                 help='URL where to fetch license, using curl (tftp, http etc)',
                                 )
        self.parser.add_argument('--reload',
                                 default=False,
                                 action="store_true",
                                 help='Reload when license is installed',
                                 )

    def run(self):
        try:
            super().run()
            res =  self.mgr.license_set(url=self.args.url, reload=self.args.reload)
            print("Result :", res)
        except self.mgr_cls.ElementException as err:
            print("Error: %s" % err)


def main(mgr_cls=None):
    util.Execute_CLI(module_name=__name__, mgr_cls=mgr_cls)
