#!/usr/bin/env python3
"""
A driver to manage Waystream iBOS elements
"""

import sys
import re
import time
from orderedattrdict import AttrDict

import emmgr.lib.log as log
import emmgr.lib.comm as comm
import emmgr.lib.emtypes as emtypes
import emmgr.lib.basedriver


class IBOS_Manager(emmgr.lib.basedriver.BaseDriver):
    
    def __init__(self, **kwargs):
        if not hasattr(self, 'model'):
            self.model = "ibos"
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
                "failed":   r"Login incorrect",
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
                self.em.before = self.em.before[:-1]
                continue
            elif match in ["disable", "enable"]:
                break
            elif match == "failed":
                raise self.ElementException("Invalid username/password", errno=self.USERNAME_PASSWORD_INVALID)

            raise self.ElementException("Error logging in, no username/password prompt")

        if match == 'disable':
            self.em.writeln("enable")
            match = self.em.expect(r"assword:")
            if match is None:
                raise self.ElementException("Error waiting for prompt after enable")
            self.em.writeln(self.enable_password)
            self.wait_for_prompt()
            
        self.em.writeln("terminal no pager")
        self.wait_for_prompt()

    def disconnect(self):
        """
        Disconnect from the element
        """
        log.debug("------------------- disconnect(%s) -------------------" % self.hostname)
        if self.transport:
            log.debug("------------------- disconnect() -------------------")
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
        if save_config:
            self.save_running_config()
        self.em.writeln("reload")
        match = self.em.expect(r"\[y/N\]\:")
        self.em.writeln("y")
        time.sleep(2)
        
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

    def license_get(self):
        # Check if there is a license
        cmd = "show license"
        out = self.run(cmd)
        if len(out):
            tmp = out[0].strip()
            tmp2 = tmp.split(":")
            if len(tmp2) > 1:
                return tmp2[1].strip()
        return None 

    def license_set(self, url=None, save_config=True, reload=None, callback=None):
        lic = self.license_get()
        if lic:
            raise self.ElementException("Element already has a license of type '%s'" % lic)

        # Get MAC address
        config_lines = self.run(cmd="show version", filter_="Base MAC address")
        if len(config_lines) < 1:
            raise self.ElementException("Cannot find system MAC address")
        tmp = config_lines[0].split(":")
        if len(tmp) < 2:
            raise self.ElementException("Cannot find system MAC address")
        mac = tmp[1].strip()

        # Fetch the license text
        url = "%s/ibos-%s.lic" % (url, mac)
        import pycurl
        from io import BytesIO
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEDATA, buffer)
        try:
            c.perform()
            c.close()
            license_text = buffer.getvalue().decode()
        except pycurl.error as err:
            raise self.ElementException("Error reading license file from %s: %s" % (url, err))
            
        # license_text = license_text.replace("\r\n", "\n")
                    
        # Add new license
        self.em.writeln("license set")
        match = self.em.expect("flash memory")

        cmd = license_text.strip()
        cmd += "\n.\n"
        out = self.run(cmd)

        # Verify that license is in place
        lic = self.license_get()
        if lic is None:
            raise self.ElementException("Error: Could not add license to element")
        
        print("reload", reload, "save_config", save_config)
        if reload:
            self.reload(save_config=save_config)
        
    # ########################################################################
    # Configuration
    # ########################################################################

    def configure(self, config_lines=None, save_running_config=False, callback=None):
        """
        Reconfigure device
        todo: trigger on  '%-ERR: <error description>'
        """
        self.connect()
        log.debug("------------------- configure() -------------------")
        config_lines = self.str_to_lines(config_lines)
        self.em.writeln("configure terminal")
        match = self.em.expect("\(config\)#")
        if match is None:
            raise self.ElementException("Error Could not enter configuration mode")
        for config_line in config_lines:
            self.em.writeln(config_line)
            match = self.em.expect("\)#")
            if match is None:
                raise self.ElementException("Error waiting for next configuration prompt")
        self.em.writeln("end")
        self.wait_for_prompt()
        if save_running_config:
            self.save_running_config()
        return True

    def get_running_config(self, filter_=None, refresh=False, callback=None):
        """
        Get config lines from running-config
        returns a list with lines, optionally filtering lines with a regex
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
        Save running-config as startup-config
        """
        if callback:
            callback("Save running-config as startup-config, hostname %s" % self.hostname)
        self.run("copy running-config startup-config")
        return True

    def set_startup_config(self, config_lines=None, callback=None):
        """
        Copy config_lines to startup_config
        """
        raise self.ElementException("Not implemented")
        
    # ########################################################################
    # Interface management
    # ########################################################################

    def interface_clear_config(self, interface=None, save_running_config=False, callback=None):
        """
        iBOS does not have any command to reset interface config 
        Get all interface config and try to remove them
        """
        for i in range(1,3):
            cmd = "show running-config context interface %s" % interface
            lines = self.run(cmd)
            if len(lines) < 4:
                break

            cmd = ["interface %s" % interface]
            for line in lines:
                if line and line[0] != "!" and not line.startswith("interface "):
                    line = line.strip()
                    if line.startswith("no "):
                        cmd.append(line[3:])
                    else:
                        cmd.append("no %s" % line)
            
            lines = self.configure(config_lines=cmd, save_running_config=save_running_config, callback=callback)

    def interface_get_admin_state(self, interface=None):
        """
        Returns the interface admin state
        """
        raise self.ElementException("Not implemented")
        
    # use default method
    # def interface_set_admin_state(self, interface=None, enabled=None):
        
    # ########################################################################
    # Topology
    # ########################################################################

    def l2_peers(self, interface=None, default_domain=None):
        """
        Returns the device L2 neighbours, using LLDP and PFDP.
        LLDP is checked first, then PFDP. PFDP only complements peers that
        does not exist in LLDP.
        """

        peers = emtypes.Peers()

        cmd = "show lldp neighbours"
        if interface:
            cmd += " interface " + interface
        lines = self.run(cmd=cmd)
        peer = None
        ix = 0
        while ix < len(lines):
            line = lines[ix]
            ix += 1
            if line.startswith('Interface:'):
                # New peer, save old
                if peer:
                    peers.add(peer)

                tmp = line.split()
                peer = emtypes.Peer(local_if=tmp[1][:-1])
                while ix < len(lines):
                    line = lines[ix]
                    ix += 1
                    if line.startswith("Interface:"):
                        # next peer
                        ix -= 1
                        break
                    tmp = line.strip().split()
                    # print(tmp)
                    if len(tmp) > 1:
                        key = tmp[0].lower()
                        if key == "chassisid:":
                            peer.remote_mac = tmp[2]
                        elif key == "sysname:":
                            peer.remote_hostname = tmp[1]
                            if "." not in peer.remote_hostname and default_domain:
                                peer.remote_hostname += "." + default_domain
                        elif key == "sysdescr:":
                            peer.remote_description = line.strip().split(None,1)[1]
                        elif key == "mgmtip:":
                            peer.remote_ipaddr = tmp[1]
                        elif key == "portid:":
                            peer.remote_if = tmp[2]

        # If new peer, save old
        if peer:
            peers.add(peer)
        
        # Todo, check PFDP peers
        #lines = self.run(cmd="show pfdp neighbours detailed")
        #for line in lines:
        #    print(line)

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
        cmd = "show interface description | include ^vlan"
        lines = self.run(cmd)
        for line in lines:
            tmp = line.split(None, 4)
            vlan = int(tmp[0][4:])
            if len(tmp) > 4:
                name = tmp[4]
            else:
                name = ""
            res[vlan] = AttrDict(id=vlan, name=name)
        return res
    
    def vlan_create(self, vlan=None, name=None):
        """
        Create a VLAN in the element
        """
        cmd = ["interface vlan%s" % vlan]
        if name:
            cmd.append("description %s" % name)
        cmd.append("no shutdown")
        self.configure(cmd, save_running_config=True)
    
    def vlan_delete(self, vlan=None):
        """
        Delete a VLAN in the element
        """
        cmd = ["no interface vlan%s" % vlan]
        self.configure(cmd, save_running_config=True)
    
    def vlan_interface_get(self, interface=None):
        """
        Get all VLANs on an interface
        Returns a dict, key is vlan ID
        """
        res = AttrDict()
        cmd = "show running-config context interface %s" % interface
        lines = self.run(cmd)
        for line in lines:
            line = line.strip()
            # print("line", line)
            if line.startswith("vlan member "):
                tmp = line[12:]
                for t1 in tmp.split(","):
                    t2 = t1.split("-")
                    vid1 = int(t2[0])
                    if len(t2) > 1:
                        vid2 = int(t2[1])
                        for t3 in range(vid1, vid2+1):
                            res[t3] = self.VLAN(id=t3)
                    else:
                        res[vid1] = self.VLAN(id=vid1)
            elif line.startswith("vlan untagged "):
                tmp = line[14:].strip()
                vid = int(tmp)
                res[vid].tagged = False
        return res
        
    def vlan_interface_create(self, interface=None, vlan=None, tagged=True):
        """
        Create a VLAN on an interface
        """
        cmd = ["interface %s" % interface]
        cmd.append("vlan member %s" % vlan)
        if not tagged:
            cmd.append("vlan untagged %s" % vlan)
        self.configure(cmd, save_running_config=True)
    
    def vlan_interface_delete(self, interface=None, vlan=None):
        """
        Delete a VLAN from an interface
        """
        cmd = ["interface %s" % interface]
        cmd.append("no vlan member %s" % vlan)
        self.configure(cmd, save_running_config=True)
    
    # def vlan_interface_set_native(self, interface=None, vlan=None):
    #     """
    #     Set native VLAN on an Interface
    #     """
    #     raise self.ElementException("Not implemented")
        
    # ########################################################################
    # File management
    # ########################################################################

    def file_list(self, filter_=None, callback=None):
        """
        List all files on the element
        """
        if filter_:
            r = re.compile(filter_)
        msg = self.run("ls flash:")
        state = 1
        file_list = []
        for line in msg:
            if state == 1:
                if line.startswith("---"):
                    state = 2
            elif state == 2:
                tmp = line.split()
                if len(tmp) < 1:
                    return file_list
                f = tmp[4]
                if filter_:
                    if r.search(f):
                        file_list.append(f)
                else:
                    file_list.append(f)
        return file_list

    def file_copy_to(self, mgr=None, filename=None, dest_filename=None, callback=None):
        """
        Copy file to element
        """
        if callback:
            callback("Copy file %s to element" % (filename))
        self.connect()
        if self.sw_exist(filename):
            return  # already on device
         
        cmd = "copy %s/%s flash:%s" % (mgr, filename, dest_filename)
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
                                "copying": r'Writing file .*\r\n', 
                                "done":    r'Transferred.*\r\n', 
                                "error":   r"%Error.*\r\n"})
            if match is None:
                raise self.ElementException("File transfer finished incorrect, self.before=%s" % self.em.before )
            if match == "copying":
                if callback is not None:
                    callback(block)     # todo, use match
                continue
            elif match == "done":
                if callback:
                    callback("Copying done, copied %s block" % block)
                break
            elif match == "error":
                raise self.ElementException("File transfer did not start. search buffer: %s" % self.em.before)
        self.wait_for_prompt()

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
        self.connect()
        lines = self.run("show version ; i Intelligent")
        if len(lines):
            tmp = lines[0].split()
            return tmp[-1]
        return None

    def sw_get_boot(self):
        """
        Get firmware image that will be loaded next reboot
        """
        self.connect()
        lines = self.run("show boot")
        if len(lines) < 1:
            raise self.ElementException("Can't find boot image")
        tmp = lines[0].split("=")
        if len(tmp) < 2:
            raise self.ElementException("Can't find boot image")
        if tmp[0] != 'boot':
            raise self.ElementException("Can't find boot image")
        return tmp[1]

    def sw_list(self, filter_=None, callback=None):
        """
        Get a list of all firmware in the element
        """
        if filter_ is None:
            filter_ = self.get_definition("firmware_filter")
        return self.file_list(filter_=filter_)

    def sw_copy_to(self, mgr=None, filename=None, dest_filename=None, callback=None):
        """
        Copy software to the element
        
        copy tftp://10.10.16.50/ibos-ms4k-6.3.11-ED-R.bz2 flash:
        """

        if callback:
            callback("Copy file %s to element" % (filename))
        self.connect()
        if filename != "bootloader" and self.sw_exist(filename):
            return  # already on device

        if not dest_filename:
            dest_filename = 'flash:'    # todo from settings
                 
        cmd = "copy %s/%s %s" % (mgr, filename, dest_filename)
        self.em.writeln(cmd)
        copied_bytes = 0
        re_copied_bytes = re.compile(r"(\d+)\/(\d+)")
        while True:
            # catch copied bytes, each output has a \r. when done a \r\n is received
            # 47104/561827\r101376/561827\r156672/561827\r211968/561827\r243712/561827\r297984/561827\r352256/561827\r405504/561827\r460800/561827\r515072/561827\r\n
            match = self.em.expect({
                                    "done":    r'Transferred.*\r\n', 
                                    "error":   r"%Error.*\r\n",
                                    "copying": r'\d+.\d+\r'
                                    })
            if match is None:
                raise self.ElementException("File transfer finished incorrectly, self.before=%s" % self.em.before )
            if match == "copying":
                if callback is not None:
                    tmp = re_copied_bytes.search(self.em.before)
                    if tmp:
                        copied_bytes = tmp.group(1)
                        callback("Copied %s of %s bytes" % (copied_bytes, tmp.group(2)))
                continue
            elif match == "done":
                if callback:
                    callback("Copying done, copied %s bytes" % copied_bytes)
                break
            elif match == "error":
                raise self.ElementException("File transfer did not start. search buffer: %s" % self.em.before)
        self.wait_for_prompt()

    def sw_copy_from(self, mgr=None, filename=None, callback=None):
        """Copy software from the element"""
        raise self.ElementException("Not implemented")
        self.connect()
        if not self.exist(filename):
            raise self.ElementException("File %s does not exist on element" % filename)
        
    def sw_set_boot(self, filename, callback=None):
        """
        Check if filename exist in element
        If True configure element to boot with the filename
        """
        self.connect()
        if not self.sw_exist(filename):
            raise self.ElementException("Error cant change boot software, filename %s does not exist" % filename)

        # Get current boot sw
        lines = self.run("show boot")
        if len(lines) < 1:
            raise self.ElementException("Can't find current bootfile")
        tmp = lines[0].split("=")
        if len(tmp) != 2:
            raise self.ElementException("Can't find current bootfile")
        if filename == tmp[1]:
            return True

        cmd = "boot system flash:%s" % filename
        self.configure(cmd)
        return True

    def sw_delete(self, filename, callback=None):
        """
        Delete file from flash
        """
        self.connect()
        if not self.sw_exist(filename):
            raise self.ElementException("File %s not found in flash" % filename)
        
        boot_firmware = self.sw_get_boot()
        if boot_firmware == filename:
            raise self.ElementException("Cannot remove file %s, it is used during boot" % filename)

        cmd = "delete flash:%s" % filename
        self.run(cmd)

    def sw_delete_unneeded(self, callback=None):
        """
        Delete unneeded firmware, so we have room for installing a new one
        This method keeps the one specified to boot
        """
        bootimg = self.sw_get_boot()
        files = self.sw_list()
        deleted = []

        if bootimg not in files:
            raise self.ElementException("Boot image does not exist in flash")
        
        for f in files:
            if f != bootimg:
                log.debug("Deleting file %s" % f)
                deleted.append(f)
                self.sw_delete(f)
        return deleted

    def sw_upgrade(self, mgr=None, filename=None, set_boot=True, callback=None):
        """
        Helper function. Uploads filename, set filename to boot
        """
        bootimg = self.sw_get_boot()
        if bootimg == filename:
            return True

        if not self.sw_exist(filename):
            # Make sure we have room for a new image
            self.sw_delete_unneeded()

            # Copy the actual file
            self.sw_copy_to(mgr=mgr, filename=filename, callback=callback)

        if set_boot:
            # Enable new image
            self.sw_set_boot(filename)
            
    def get_bootloader(self, callback=None):
        """       
        Returns current bootloader

        Two formats:
        1)
            show version | i ^Bootloader
            Bootloader version: asrboot-asr5k-3.1.4-R
        2)
            show version | i ^Bootloader
            Bootloader version: asrboot-asr6k-4.0.3-R
            Bootloader version on flash: asrboot-asr6k-4.0.4-R

        We always return the "Bootloader version:"
        
        2) Seems to show up when bootloader on flash is different than running bootloader
        """
        self.connect()
        cmd = 'show ver | include "^Bootloader version:"'
        lines = self.run(cmd)
        if len(lines) != 1:
            raise self.ElementException("Cannot find bootloader in use: %s" % lines)
        
        # "Bootloader version: msboot-ms4k-4.0.3-R"
        tmp = lines[0].split(':')
        if len(tmp) != 2:
            raise self.ElementException("Cannot find bootloader in use: %s" % tmp)
        return tmp[1].strip()
        

    def set_bootloader(self, mgr=None, filename=None, callback=None):
        """
        Copies bootloader to element and activate it
        
        copy tftp://10.10.16.50/msboot-ms4k-3.7.6-R.bin bootloader 
        517120/561821
        Verifying checksum of downloaded bootloader.
        Writing downloaded bootloader to flash (this may take a few seconds).
        Verifying checksum of bootloader on flash.
        Execute command 'reload' to start new bootloader.
        Transferred 561821 bytes successfully in 5 seconds
        """

        return self.sw_copy_to(mgr=mgr, filename=filename, dest_filename='bootloader', callback=callback)
            

Driver = IBOS_Manager   # Easy access

if __name__ == '__main__':
    sys.argv.append("-m ibos")
    import emmgr.lib.cli
    emmgr.lib.cli.main(Driver)
