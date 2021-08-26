#!/usr/bin/env python3
"""
A driver to manage Cisco IOS and IOS-XE elements
"""

import sys
import re
from orderedattrdict import AttrDict

import emmgr.lib.log as log
import emmgr.lib.comm as comm
import emmgr.lib.emtypes as emtypes
import emmgr.lib.basedriver


class IOS_Manager(emmgr.lib.basedriver.BaseDriver):
    
    def __init__(self, **kwargs):
        if not hasattr(self, 'model'):
            self.model = "ios"
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

        # % Authentication failed

        while True:
            match = self.em.expect({ 
                "failed":   r"Authentication failed",
                "username": r"sername:", 
                "password": r"assword:", 
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

        if match == "disable":
            self.em.writeln("enable")
            match = self.em.expect(r"assword:")
            if match is None:
                raise self.ElementException("Error waiting for prompt after enable")
            self.em.writeln(self.enable_password)
            
        self.em.writeln("terminal length 0")
        self.wait_for_prompt()
        self.em.writeln("terminal width 0")
        self.wait_for_prompt()

    def disconnect(self):
        """
        Disconnect from the element
        """
        log.debug("------------------- disconnect(%s) -------------------" % self.hostname)
        if self.transport:
            # self.em.writeln("logout")
            self.em = None
            self.transport.disconnect()
            self.transport = None
            
    def reload(self, save_config=True, callback=None):
        """
        Reload the element. If running-config is unsaved, option to save it
        """
        self.connect()
        log.debug("------------------- reload() -------------------")
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

    def run(self, cmd=None, filter_=None, timeout=None, callback=None):
        """
        Run a command on element
        returns a list with configuration lines, optionally filtering lines with a regex
        """
        self.connect()
        log.debug("------------------- run() -------------------")
        self.em.writeln(cmd)
        self.wait_for_prompt()
        output = self.em.before.split("\r\n")
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
        self.em.writeln("configure terminal")
        self.wait_for_prompt()
        for config_line in config_lines:
            self.em.writeln(config_line)
        self.em.writeln("end")
        self.wait_for_prompt()
        if save_running_config:
            self.save_running_config()
        return True

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
        
    def set_startup_config(self, config_lines=None, callback=None):
        """
        Set the startup_configuration to config_lines (list)
        """
        raise self.ElementException("Not implemented")

    # ########################################################################
    # Interface management
    # ########################################################################

    # use default method
    # def interface_clear_config(self, interface):

    def interface_get_admin_state(self, interface, enabled):
        """
        Default driver that enables/disables a interface
        This default driver is used if there is a CLI command for this.
        """
        raise self.ElementException("Not implemented")
        
    # use default method
    # def interface_set_admin_state(self, interface, enabled):

    # ########################################################################
    # Topology
    # ########################################################################

    class Peer:
        def __init__(self, hostname=None, 
                    ipaddr_mgmt=None,
                    local_if=None, 
                    remote_if=None, 
                    remote_platform=None):
            self.hostname = hostname
            self.ipaddr_mgmt = ipaddr_mgmt
            self.local_if = local_if
            self.remote_if = remote_if
            self.remote_platform = remote_platform
            
        def __str__(self):
            return "Peer(hostname %s, local_if %s, remote_if %s, remote_platform %s)" % \
               (self.hostname, self.local_if, self.remote_if, self.remote_platform)

    def add_peer(self, peers, peer):
        if peer is None:
            return
        if peer.local_if:
            key = peer.local_if
        else:
            key = peer.hostname
        peers[key] = peer

    def _l2_peers_get_sections(self, lines):
        """
        Return tuples with sections, one for each peer, using ---- as divider
        """
        row_ix = []
        ix = 0
        while ix < len(lines):
            line = lines[ix]
            if line and line[0] == "-":
                row_ix.append(ix+1)
            ix += 1
        sections = []
        for ix in range(0, len(row_ix)):
            if ix == len(row_ix) - 1:
                sections.append( (row_ix[ix], len(lines)) )
            else:
                sections.append( (row_ix[ix], row_ix[ix+1]) )
        return sections


    def l2_peers(self, interface=None, default_domain=None):
        """
        Returns the device L2 neighbours, LLDP and CDP
        """
        peers = emtypes.Peers()

        # ----- LLDP -----
        if interface:
            cmd = "show lldp neighbors %s detail" % interface
        else:
            cmd = "show lldp neighbors detail"
        lines = self.run(cmd=cmd)
        sections = self._l2_peers_get_sections(lines)

        ix = 0
        for start,stop in sections:
            peer = emtypes.Peer(local_if="")
            for line in lines[start:stop]:
                # print(line)
                if line.startswith("Local Intf:"):
                    peer.local_if = line[11:].strip()
                elif line.startswith("Chassis id:"):
                    peer.remote_mac = line[11:].strip()
                elif line.startswith("Port id:"):
                    peer.remote_if = line[8:].strip()
                elif line.startswith("System Name:"):
                    peer.remote_hostname = line[12:].strip()
                    if default_domain and "." not in peer.remote_hostname:
                        peer.remote_hostname += "." + default_domain
                elif line.startswith("System Description:"):
                    peer.remote_description = lines[start+1]
                elif line.startswith("Management Addresses:"):
                    peer.remote_ipaddr = lines[start + 1].strip().split()[1]
                start += 1
            if peer.local_if:
                peers.add(peer)
            else:
                log.warning("Cannot add peer, no local_if. %s" % peer)
        
        # ----- CDP -----
        if interface:
            cmd = "show cdp neighbors %s detail" % interface
        else:
            cmd = "show cdp neighbors detail"
        lines = self.run(cmd=cmd)
        sections = self._l2_peers_get_sections(lines)

        ix = 0
        for start,stop in sections:
            peer = emtypes.Peer(remote_mac="")
            for line in lines[start:stop]:
                # print(line)
                if line.startswith("Device ID:"):
                    peer.remote_hostname = line[11:].strip()
                    if default_domain and "." not in peer.remote_hostname:
                        peer.remote_hostname += "." + default_domain
                if line.startswith("Platform:"):
                    peer.remote_description = line[9:].strip().split(",")[0]
                elif line.startswith("Interface:"):
                    tmp = line.split()
                    peer.local_if = tmp[1].replace(",", "")
                    peer.remote_if = tmp[6].replace(",", "")
                elif line.startswith("  IP address:"):
                    peer.remote_ipaddr = line[13:].strip()
            if peer.local_if:
                if not peers.exists(peer):
                    peers.add(peer)
                else:
                    log.warning("Peer %s already added, through LLDP" % peer)
            else:
                log.warning("Cannot add peer, no local_if. %s" % peer)

        return peers

    # ########################################################################
    # VLAN management
    # ########################################################################

    class VLAN:
        def __init__(self,
                     id=None,
                     name=None,
                     tagged=True):
            self.id = id
            self.name = name
            self.tagged = tagged

        def __str__(self):
            return "VLAN(id=%s, tagged=%s, name=%s)" % (self.id, self.tagged, self.name)

    def vlan_get(self):
        """
        List all VLANs in the element
        Returns a dict, key is vlan ID
        """
        res = AttrDict()
        cmd = "show vlan brief"
        lines = self.run(cmd)
        for line in lines:
            tmp = line.split(None, 2)
            # print(tmp)
            if len(tmp) > 2:
                try:
                    vlan = int(tmp[0])
                    name = tmp[1]
                    res[vlan] = self.VLAN(id=vlan, name=name, tagged=None)
                except ValueError:
                    pass
        return res
    
    def vlan_create(self, vlan, name):
        """
        Create a VLAN in the element
        """
        raise self.ElementException("Not implemented")
    
    def vlan_delete(self, vlan):
        """
        Delete a VLAN in the element
        """
        raise ElementException("Not implemented")
    
    def vlan_interface_get(self, interface=None):
        """
        Get all VLANs on an interface
        Returns a dict, key is vlan ID
        """
        vlans = AttrDict()
        untagged_vlan = None
        cmd = "show running-config interface %s" % interface
        lines = self.run(cmd)
        for line in lines:
            line = line.strip()
            # print("line", line)
            if line.startswith("switchport trunk allowed vlan "):
                tmp = line[30:]
                if tmp.startswith("add "):
                    tmp = tmp[4:]
                for t1 in tmp.split(","):
                    t2 = t1.split("-")
                    vid1 = int(t2[0])
                    if len(t2) > 1:
                        vid2 = int(t2[1])
                        for t3 in range(vid1, vid2+1):
                            vlans[t3] = self.VLAN(id=t3)
                    else:
                        vlans[vid1] = self.VLAN(id=vid1)
            elif line.startswith("switchport trunk native vlan "):
                untagged_vlan = int(line[29:].strip())
        if untagged_vlan:
            if untagged_vlan in vlans:
                vlans[untagged_vlan].tagged = False
            else:
                vlans[untagged_vlan] = self.VLAN(id=untagged_vlan, tagged=False)
        return vlans

    def vlan_interface_create(self, interface, vlan, tagged=True):
        """
        Create a VLAN to an interface
        """
        cmd = ["interface %s" % interface]
        cmd.append("switchport trunk allowed vlan add %s" % vlan)
        if not tagged:
            cmd.append("switchport trunk native vlan %s" % vlan)
        self.configure(cmd, save_running_config=True)
    
    def vlan_interface_delete(self, interface, vlan):
        """
        Delete a VLAN from an interface
        """
        cmd = ["interface %s" % interface]
        cmd.append("switchport trunk allowed vlan remove %s" % vlan)
        self.configure(cmd, save_running_config=True)
    
    def vlan_interface_set_native(self, interface, vlan):
        """
        Set native VLAN on an Interface
        """
        raise self.ElementException("Not implemented")

    # ########################################################################
    # Software management
    # ########################################################################
    
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
        if filter_ is None:
            filter_ = self.get_definition("firmware_filter")
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
        """
        Copy software to the element
        """
        
        if callback:
            callback("Copy file %s to element" % (filename))
        self.connect()
        if self.sw_exist(filename):
            return  # already on device
         
        cmd = "copy %s/%s %s" % (mgr, filename, dest_filename)
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
        Copy software from the element
        """
        raise self.ElementException("Not implemented")
        self.connect()
        if not self.sw_exist(filename):
            raise self.ElementException("File %s does not exist on element" % filename)

    def sw_delete(self, filename, callback=None):
        """
        Delete filename from element
        """
        self.connect()
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
            raise self.ElementException("Unexpected state, can't find command that selects operating system (1)")
        line = lines[0].strip()
        p = line.find(":")
        if p < 0:
            raise self.ElementException("Unexpected state, can't find command that selects operating system (2)")
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
            raise self.ElementException("Error cant change boot software, filename %s does not exist" % filename)
        
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
    sys.argv.append("-m ios")
    import emmgr.driver.cli as cli
    cli.main(IOS_Manager)
