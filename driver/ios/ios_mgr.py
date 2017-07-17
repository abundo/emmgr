#!/usr/bin/env python3
"""
A driver to manage Cisco IOS and IOS-XE elements
"""

import sys
import re

import emmgr.lib.config as config
import emmgr.lib.log as log
import emmgr.lib.util as util
import emmgr.lib.comm as comm

from emmgr.driver.basedriver import BaseDriver


class IOS_Manager(BaseDriver):
    
    # ------------------------------------------------------------
    # Generic methods
    # ------------------------------------------------------------

    def connect(self):
        """
        Connect to the element using telnet or ssh
        login, go to enable mode
        """
        if self.transport:
            # todo verify connectivity
            return

        if self.use_ssh:
            if self.port == None: self.port = 22
            self.transport = comm.RemoteConnection(timeout=20, method="ssh")
        else:
            if self.port == None: self.port = 23
            self.transport = comm.RemoteConnection(timeout=20, method="telnet")
            
        self.transport.connect(self.hostname, self.username)
        self.em = comm.Expect(self.transport)

        if not self.use_ssh:
            # telnetlib does no login
            match = self.em.expect(r"sername:")
            if match is None:
                raise comm.CommException(1, "Error waiting for username prompt")
            self.em.writeln(self.username)

        match = self.em.expect(r"assword:")
        if match is None:
            raise comm.CommException(1, "Error waiting for password prompt")
        self.em.writeln(self.password)
    
        # Wait for CLI prompt
        match = self.em.expect( { "disable": r">", "enable": r"#"} )
        if match is None:
            raise comm.CommException(1, "Error waiting for CLI prompt")
        
        if match == 'disable':
            # Non-privileged mode, goto enable mode
            self.em.writeln("enable")
            match = self.em.expect(r"assword:")
            if match is None:
                raise comm.CommException(1, "Error waiting for prompt after enable")
            self.em.writeln(self.enable_password)
            self.wait_for_prompt()
            
        self.em.writeln("terminal length 0")
        self.wait_for_prompt()
        self.em.writeln("terminal width 0")
        self.wait_for_prompt()

    def disconnect(self):
        """Disconnect from the element"""
        if self.transport:
            self.em.writeln("logout")
            self.em = None
            self.transport.disconnect()
            self.transport = None
            
    def wait_for_prompt(self):
        log.debug("------------------- wait_for_prompt() -------------------")
        match = self.em.expect("#")
        return match

    def configure(self, config_lines, save_running_config=False, callback=None):
        """Reconfigure device"""
        self.connect()
        log.debug("------------------- configure() -------------------")
        self.em.writeln("configure terminal")
        match = self.em.expect(".*Z\.")
        if match is None:
            raise comm.CommException(1, "Error Could not enter configuration mode")
        for config_line in config_lines:
            self.em.writeln(config_line)
        self.em.writeln("end")
        self.wait_for_prompt()
        if save_running_config:
            self.save_running_config()
        return True

    def run(self, cmd=None, filter_=None, callback=None):
        self.connect()
        self.em.writeln(cmd)
        self.wait_for_prompt()
        output = self.em.before.split("\n")
        return self.filter_(output, filter_)

    def get_running_config(self, filter_=None, refresh=False, callback=None):
        """
        Get config lines from running-config, optionally filtering with a regex
        returns a list
        """
        log.debug("------------------- get_running_config() -------------------")
        if not refresh and self.running_config is None:
            self.running_config = self.run("show running-config")
        
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
        Store running-config as startup-config
        """
        if callback:
            callback("Save running-config as startup-config, hostname %s" % self.hostname)
        self.connect()
        self.em.writeln("copy running-config startup-config")
        self.em.expect("startup-config")
        self.em.writeln("")
        self.em.expect("[OK]")
        self.wait_for_prompt()
        return True
        
    def reload(self, save_config=True, callback=None):
        """Reload the element. If running-config is unsaved, option to save it"""
        self.connect()
        self.em.writeln("reload")
        
        while True:
            match = self.em.expect( {
                    "confirm": "yes/no",
                    "reloading": "confirm",
                    "reloading1": "closed by remote host", 
                    "reloading2": "closed by foreign host", 
                    "reloading3": "Reload command.", 
                    })
            log.debug("Reload match: %s" % match)
            if match == "reloading":
                self.em.writeln("y")

            elif match == "confirm":
                # configuration is not saved, do so
                if save_config:
                    self.em.writeln("y")
                else:
                    self.em.writeln("n")
            else:
                break
        
        # Force the connection closed
        self.em = None
        self.transport.disconnect()
        self.transport = None

    # ------------------------------------------------------------
    # Software management
    # ------------------------------------------------------------

    def sw_list(self, filter_=None, callback=None):
        """
        Get a list of all firmware in the element
        """
        self.connect()
        self.em.writeln("dir flash:")
        self.em.expect(r"Directory of .*\r\n")
        self.em.expect("bytes free")
        msg = self.em.before
        self.wait_for_prompt()

        # lets parse names, we ignore a bunch of names and directories
        sw_list = []
        if filter_:
            r = re.compile(filter_)
        for line in msg.split("\r\n"):
            if line:
                tmp = line.split()
                if tmp[1:3] == ['bytes', 'total']:
                    break 
                if "d" in tmp[1]:    # directory?
                    continue
                f = tmp[-1]
                if filter_:
                    if r.search(f):
                        sw_list.append(f)
                else:
                    sw_list.append(f)
        return sw_list

    def sw_copy_to(self, mgr=None, filename=None, dest_filename="bootflash:", callback=None):
        """Copy software to the element"""
        
        if callback:
            callback("Copy file %s to element" % (filename))
        self.connect()
        if self.sw_exist(filename):
            return  # already on device
         
        cmd = "copy %s/%s %s" % (mgr, filename, dest_filename)
        self.em.writeln(cmd)
        match = self.em.expect(r"Destination filename.*\?")
        if match is None:
            raise comm.CommException(1, "Unexpected output %s" % self.em.match)
#        self.em.writeln(dest_filename)
        self.em.writeln("")

        match = self.em.expect({
                            "accessing": r"Accessing.*\r\n", 
                            "overwrite": r"Do you want to over write\? \[confirm\]",
                            })
        if match is None:
            raise comm.CommException(1, "File transfer did not start")
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
                raise comm.CommException(1, "File transfer finished incorrect, self.before=%s" % self.em.before )
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
                raise comm.CommException(1, "File transfer did not start. search buffer: %s" % self.em.before)
        self.wait_for_prompt()

    
    def sw_copy_from(self, mgr=None, filename=None, callback=None):
        """Copy software from the element"""
        raise comm.CommException(1, "Not implemented")
        self.connect()
        if not self.sw_exist(filename):
            raise comm.CommException(1, "File %s does not exist on element" % filename)

    def sw_delete(self, filename, callback=None):
        """Delete filename from flash"""
        self.connect()
        if not self.sw_exist(filename):
            raise comm.CommException(1, "File %s not found in flash" % filename)
        
        # todo, check so we dont remove the current filename
        # conf = self.getRunningConfig(filter="^boot system flash")

        cmd = "delete flash:%s" % filename
        self.em.writeln(cmd)
        
        match = self.em.expect({
                            "confirm": r"Delete filename.*\?"
                            })
        if match is None:
            raise comm.CommException(1, "Error deleting filename %s" % filename)
        
        if match == "confirm":
            self.em.writeln("")

        match = self.em.expect({
                    "confirm": "Delete.*\[confirm\]",
                    })
        if match is None:
            raise comm.CommException(1, "Unexpected response, seach buffer: %s" % self.em.before)

        self.em.write("y")            # confirm deletion
        self.wait_for_prompt()

    def sw_delete_unneeded(self, callback=None):
        """
        Delete unneeded firmware
        We keep the one pointed to by "boot system flash" and the currently running one
        """
        self.connect()
        keep = {}
        bootflash = {}
        deleted = []
        files = self.sw_list()

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
            raise comm.CommException(1, "Unexpected state, can't find command that selects operating system (1)")
        line = lines[0].strip()
        p = line.find(":")
        if p < 0:
            raise comm.CommException(1, "Unexpected state, can't find command that selects operating system (2)")
        filename = line[p+1:-1]
        if filename[0] == "/":
            filename = filename[1:]
        # print("line", line)
        # print("filename", filename)
        
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
                self.sw_delete(f)
                if f in bootflash:
                    self.configure("no " + bootflash[f])
        return deleted

    def sw_set_boot(self, filename, callback=None):
        """
        Check if filename exist in element
        if true configure element to boot with the filename
        """
        self.connect()
        if not self.sw_exist(filename):
            raise comm.CommException(1, "Error cant change boot software, filename %s does not exist" % filename)
        
        # remove old boot system flash commands
        lines = self.getRunningConfig(filter_="^boot system flash ")
        for line in lines[1:]:
            print("   no " + line)
            self.configure("no " + line)

        # set new boot system flash        
        cmd = "boot system flash %s" % filename
        self.configure(cmd)
        self.wait_for_prompt()

    def sw_upgrade(self, mgr=None, filename=None, setboot=True, callback=None):
        """
        Helper function. Uploads filename, set filename to boot, save running-config
        """
        if not self.sw_exist(filename):
            self.sw_copy_to(mgr=mgr, filename=filename, callback=callback)

        if setboot:
            self.sw_set_boot(filename)
            self.save_running_config(callback=callback)

Driver = IOS_Manager

if __name__ == '__main__':
    import emmgr.driver.cli as cli
    cli.main(IOS_Manager)
