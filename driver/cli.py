#!/usr/bin/env python3
'''
Driver test CLI, used by drivers

todo, if no password, ask for it, NOT echoing to TTY
'''

import sys
import re

import emmgr.lib.config as config
import emmgr.lib.log as log
import emmgr.lib.util as util
import emmgr.lib.comm as comm

hostconfig = config.em.scriptaccount

class BaseCLI(util.BaseCLI):
    
    def __init__(self, **kwargs):
        self.mgr_class = kwargs.pop("mgr_class")
        super().__init__(**kwargs)
        
        log.setLevel(self.args.loglevel)
        
        if self.args.hostname is None and self.args.ip is None:
            util.die("Error: You need to specify -H/--hostname or -i/--ip")
            
        hostconfig['hostname'] = self.args.hostname
        self.mgr = self.mgr_class(**hostconfig)


    def add_arguments2(self):
        self.parser.add_argument('-H', '--hostname',
                                 help='Hostname of element')
        self.parser.add_argument('-i', '--ip',
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


class CLI_configure(BaseCLI):
    
    def add_arguments(self):
        self.parser.add_argument('-c', '--config',
                                 required=True,
                                 action="append",
                                 help='New configuration',
                                 )

    def run(self):
        res =  self.mgr.configure(config_lines=self.args.config)
        print("Result :", res)


class CLI_run(BaseCLI):
    
    def add_arguments(self):
        self.parser.add_argument('-c', '--command',
                                 required=True,
                                 help='Command to run',
                                 )

    def run(self):
        lines =  self.mgr.run(cmd=self.args.command)
        if lines:
            print("Output from command:", self.args.command)
            for line in lines:
                print(line)
        else:
            print("No output")


class CLI_get_running_config(BaseCLI):

    def run(self):
        lines = self.mgr.get_running_config()
        print("Running configuration:")
        if lines:
            for line in lines:
                print(line)
        else:
            print("No output")


class CLI_save_running_config(BaseCLI):

    def run(self):
        res = self.mgr.save_running_config()
        print("Result :", res)


class CLI_reload(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("-s", "--save_config",
                                 action="store_true",
                                 help='Save current config to startup config',
                                 default=False)

    def run(self):
        res = self.mgr.reload(save_config=self.args.save_config)
        print("Result :", res)


class CLI_interface_clear_config(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument("--interface",
                                 help='Interface to clear',
                                 )

    def run(self):
        res = self.mgr.interface_clear_config(interface=self.args.interface)
        print("Result :", res)


class CLI_sw_exist(BaseCLI):
    def add_arguments(self):
        self.parser.add_argument('-f', '--filename',
                                 required=True,
                                 help='Filename',
                                 )

    def run(self):
        res = self.mgr.sw_exist(self.args.filename)
        print("Does firmware %s exist ? " % self.args.filename, res)


class CLI_sw_list(BaseCLI):

    def add_arguments(self):
        self.parser.add_argument('--filter',
                            help='Filter out firmware names',
                            default=None)

    def run(self):
        sw_list = self.mgr.sw_list(filter_=self.args.filter)
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
        res = self.mgr.sw_copy_to(mgr=self.args.server, 
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
            res = self.mgr.sw_set_boot(self.args.filename)
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
            res = self.mgr.sw_delete(self.args.filename)
            print("File deleted:", res)
        except comm.CommException as e:
            print("Error, %s" % (e.message))


class CLI_sw_delete_unneeded(BaseCLI):

    def run(self):
        try:
            deleted = self.mgr.sw_delete_unneeded()
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
                                 help='Server to copy from/to',
                                 )
    def run(self):
        if self.args.filename is None:
            raise comm.CommException(1, "Must specify filename")
        res = self.mgr.sw_upgrade(mgr=self.args.server, 
                                 filename=self.args.filename,
                                 callback=self.callback,
                                 )
        print("sw_upgrade status:", res)

    def callback(self, status):
        print("   ", status)


def main(MgrClass):
    c = util.MyCLI(__name__, mgr_class=MgrClass)
