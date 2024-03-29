#!/usr/bin/env python3
"""
A driver to manage CTS systems elements
"""

import sys
import re

import emmgr.lib.log as log
import emmgr.lib.comm as comm
import emmgr.lib.basedriver


class CTS_Manager(emmgr.lib.basedriver.BaseDriver):
    
    def __init__(self, **kwargs):
        if not hasattr(self, 'model'):
            self.model = "vrp"
        kwargs["newline"] = "\r\n"
        super().__init__(**kwargs)

    # ########################################################################
    # Generic
    # ########################################################################

    def connect(self):
        """
        Connect to the element using telnet or ssh
        login, go to enable mode
        """
        if self.em:
            return
        super().connect()


        while True:
            match = self.em.expect({ 
                "failed":   r"denied",
                "username": r"sername: ", 
                "password": r"assword: ", 
                "disable": r">",
                "enable": r"#",
                })
            if match == "username":
                self.em.writeln(self.username)
                continue
            elif match == "password":
                self.em.writeln(self.password)
                continue
            elif match in ["disable", "enable"]:
                break
            elif match == "failed":
                raise self.ElementException("Invalid username/password", errno=self.USERNAME_PASSWORD_INVALID)

            raise self.ElementException("Error logging in, no username/password prompt")

        # Go to enable mode
        if match == "disable":
            self.em.writeln("enable")
            match = self.em.expect({ "sendpassword": r"assword: ", "continue": "3-MANAGE", "ignore": r"Error.*position." })
            if match is None:
                raise self.ElementException("Error waiting for prompt after enable")
            if match is "sendpassword":
                self.em.writeln(self.password)  # User password is enable password
            self.wait_for_prompt()
    
    def disconnect(self):
        """
        Disconnect from the element
        """
        if self.transport:
            log.debug("------------------- disconnect() -------------------")
            self.em.writeln("quit")
            self.em = None
            self.transport.disconnect()
            self.transport = None
            
    def reload(self, save_config=True, callback=None):
        """
        Reload the element. If running-config is unsaved, option to save it
        status: Todo
        """
        self.connect()
        log.debug("------------------- reload() -------------------")
        if save_config:
            self.save_running_config()
        self.em.writeln("reboot")
        self.em.expect("rebooting")
        
        # Force the connection closed
        self.em = None
        self.transport.disconnect()
        self.transport = None

    def run(self, cmd=None, filter_=None, timeout=None, callback=None):
        """
        Run a command on element
        returns a list with configuration lines, optionally filtering lines with a regex
        """
        self.connect()
        log.debug("------------------- run() -------------------")
        self.em.writeln(cmd)
        self.wait_for_prompt()
        output = self.em.before.split(self.newline)
        if len(output) > 1:
            output = output[1:-1]
        return self.filter_(output, filter_)

    # ########################################################################
    # Configuration
    # ########################################################################

    def configure(self, config_lines, save_running_config=False, callback=None):
        """
        Reconfigure device
        """
        self.connect()
        log.debug("------------------- configure() -------------------")
        config_lines = self.str_to_lines(config_lines)
        self.em.writeln("configure")
        match = self.wait_for_prompt()
        if match is None:
            raise self.ElementException("Error Could not enter configuration mode")
        for config_line in config_lines:
            self.em.writeln(config_line)
            self.wait_for_prompt()
        self.em.writeln("exit")     # Todo, multiple exit until (config) disappears from prompt?
        self.wait_for_prompt()
        if save_running_config:
            self.save_running_config()
        return True

    def get_running_config(self, filter_=None, refresh=False, callback=None):
        """
        Get config lines from running-config, optionally filtering with a regex
        returns a list
        """
        self.connect()
        log.debug("------------------- get_running_config() -------------------")
        if not refresh and self.running_config is None:
            self.running_config = self.run("display current-config", timeout=60)
        
        if filter_ is None:
            return self.running_config
        
        # filter out the lines matching
        match = [] 
        p = re.compile(filter_)
        for line in self.running_config:
            if p.search(line):
                match.append(line)
        return match

    def save_running_config(self, callback=None):
        """
        Store current-config as startup-config
        status: Todo
        """
        self.connect()
        log.debug("------------------- save_running_config() -------------------")
        if callback:
            callback("Save current-config as startup-config, hostname %s" % self.hostname)
        # self.run("write")
        self.em.writeln("write")
        match = self.em.expect("Save Config Succeeded!")
        self.wait_for_prompt()
        return True
        
    def set_startup_config(self, config_lines=None, callback=None):
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

    def vlan_list(self, vlan, name):
        """
        List all VLANs in the element
        """
        raise ElementException("Not implemented")
    
    def vlan_create(self, vlan, name):
        """
        Create a VLAN in the element
        """
        raise ElementException("Not implemented")
    
    def vlan_delete(self, vlan):
        """
        Delete a VLAN in the element
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_create(self, interface, vlan, tagged=False):
        """
        Create a VLAN to an interface
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_delete(self, interface, vlan):
        """
        Delete a VLAN from an interface
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_set_native(self, interface, vlan):
        """
        Set native VLAN on an Interface
        """
        raise ElementException("Not implemented")
     
    # ########################################################################
    # Software management
    # ########################################################################

    def sw_list(self, filter_=None, callback=None):
        """
        Get a list of all firmware in the element
        status: OK
        """
        self.connect()
        log.debug("------------------- sw_list() -------------------")
        self.em.writeln("dir flash:")
        self.em.expect("FileName")
        self.em.expect(" total ")
        msg = self.em.before
        self.wait_for_prompt()

        # lets parse names, we ignore a bunch of names and directories
        sw_list = []
        if filter_:
            r = re.compile(filter_)
        for line in msg.split("\r\n"):
            line = line.rstrip()
            if line:
                tmp = line.split()
                if tmp[1:3] == ['KB', 'total']:
                    break 
                if tmp[1][0] == "d":    # directory?
                    continue
                f = tmp[7]
                if filter_:
                    if r.search(f):
                        sw_list.append(f)
                else:
                    sw_list.append(f)
        return sw_list

    def sw_copy_to(self, mgr=None, filename=None, dest_filename="bootflash:", callback=None):
        """
        Copy file to element
        status: Todo
        """
        self.connect()
        log.debug("------------------- sw_copy_to() -------------------")
        
        if callback:
            callback("Copy file %s to element" % (filename))
        if self.swExist(filename):
            return  # already on device. verify checksum?
         
        cmd = "copy %s/%s %s" % (mgr, filename, dest_filename)
        print("cmd " + cmd)
        self.em.writeln(cmd)
        match = self.em.expect(r"Destination filename.*\?")
        if match is None:
            raise self.ElementException("Unexpected output %s" % self.em.match)
        self.em.writeln("")

        match = self.em.expect({
                            "accessing": r"Accessing.*\r\n", 
                            "overwrite": r"Do you want to over write\? \[confirm\]",
                            })
        if match is None:
            raise self.ElementException("File transfer did not start")
        if match == "overwrite":
            self.em.writeln("y")

        block = 0
        while True:
            block += 1
            if callback:
                callback("Copying file to element, block %s" % block)
            match = self.em.expect({
                                "copying": r'!', 
                                "done":    r'bytes copied', 
                                "error":   r"%Error.*\r\n"})
            if match is None:
                raise self.ElementException("File transfer finished incorrect, self.before=%s" % self.em.before )
            if match == "copying":
                if callback is not None:
                    callback(block)
                else:
                    print("!", end="")
                continue
            elif match == "done":
                if callback:
                    callback("Copying done, copied %s block" % block)
                break
            elif match == "error":
                raise self.ElementException("File transfer did not start. search buffer: %s" % self.em.before)
        self.wait_for_prompt()

    def sw_copy_from(self, mgr=None, filename=None, callback=None):
        """
        Copy file from element
        """
        raise self.ElementException("Not implemented")
        self.connect()
        log.debug("------------------- sw_copy_from() -------------------")
        if not self.sw_exist(filename):
            raise self.ElementException("File %s does not exist on element" % filename)

    def sw_delete(self, filename):
        """
        Delete filename from flash
        status: Todo
        """
        raise self.ElementException("Not implemented")
        self.connect()
        log.debug("------------------- sw_delete() -------------------")
        if not self.sw_exist(filename):
            raise self.ElementException("File %s not found in flash" % filename)

        # todo, check so we dont remove the current filename
        # conf = self.getRunningConfig(filter="^boot system flash")

        cmd = "delete flash:%s" % filename
        self.em.writeln(cmd)
        
        match = self.em.expect({
                            "confirm": r"Delete filename.*\?"
                            })
        if match is None:
            raise self.ElementException("Error deleting filename %s" % filename)
        
        if match == "confirm":
            self.em.writeln("")

        match = self.em.expect({
                    "confirm": "Delete.*\[confirm\]",
                    })
        if match is None:
            raise self.ElementException("Unexpected response, seach buffer: %s" % self.em.before)

        self.em.write("y")            # confirm deletion
        self.wait_for_prompt()

    def sw_delete_unneeded(self):
        """
        Delete unneeded firmware
        We keep the one pointed to by "boot system flash" and the currently running one
        status: Todo
        """
        raise self.ElementException("Not implemented")
        self.connect()
        log.debug("------------------- sw_delete_unneeded() -------------------")
        keep = {}
        bootflash = {}
        deleted = []
        files = self.swList()

        # Get the boot flash image
        lines = self.getRunningConfig(filter_="^boot system flash")
        for line in lines:
            filename = line[18:].strip()
            if filename in files:
                # file found in flash, candidate to keep
                if len(keep) == 0:
                    keep[filename] = True
            bootflash[filename] = line
        
        # Check the currently running firmware
        lines = self.getCommandOutput("show version", filter_="^System image file is")
        if len(lines) < 1:
            raise self.ElementException("Unexpected state, can't find command that selects operating system (1)")
        line = lines[0].strip()
        p = line.find(":")
        if p < 0:
            raise self.ElementException("Unexpected state, can't find command that selects operating system (2)")
        filename = line[p+1:-1]
        if filename[0] == "/":
            filename = filename[1:] 
             
        if filename in files:
            keep[filename] = ""
        else:
            log.warning("Host %s running firmware (%s) does not exist in flash" % (self.hostname, filename))

        for f in files:
            if f in keep:
                log.debug("Keeping file %s" % f)
            else:
                log.debug("Deleting file %s" % f)
                deleted.append(f)
                self.swDelete(f)
                if f in bootflash:
                    self.setConfig("no " + bootflash[f])
        return deleted

    def sw_set_boot(self, filename, callback=None):
        """
        Check if filename exist in element
        if true configure element to boot with the filename
        status: Todo
        """
        raise self.ElementException("Not implemented")
        self.connect()
        log.debug("------------------- sw_set_boot() -------------------")
        if not self.sw_exist(filename):
            raise self.ElementException("Error cant change boot software, filename %s does not exist" % filename)
        
        # remove old boot system flash commands
        # todo 
        # startup system-software S5300EI-V200R003C00SPC300.cc
        lines = self.get_running_config(filter_="^boot system flash ")
        for line in lines[1:]:
            print("   no " + line)
            self.setConfig("no " + line)

        # set new boot system flash        
        cmd = "boot system flash %s" % filename
        self.setConfig(cmd)
        self.wait_for_prompt()

    def sw_upgrade(self, mgr=None, filename=None, setboot=True, callback=None):
        """
        Helper function. Uploads filename, set filename to boot, save running-config
        status: Todo
        """
        raise self.ElementException("Not implemented")
        log.debug("------------------- sw_upgrade() -------------------")
        if not self.sw_exist(filename):
            self.swCopyTo(mgr=mgr, filename=filename, callback=callback)

        if setboot:
            self.sw_set_boot(filename)
            self.save_running_config(callback=callback)

Driver = CTS_Manager


if __name__ == '__main__':
    sys.argv.append("-m vrp")
    import emmgr.driver.cli as cli
    cli.main(Driver)
