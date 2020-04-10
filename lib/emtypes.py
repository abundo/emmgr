#!/usr/bin/env python3
'''
Common types
'''

import sys
import os.path
import datetime
import json
import yaml
import pprint
import argparse
import importlib.machinery
from orderedattrdict import AttrDict


class TypesException(Exception):
    pass


class MAC_Address:
    """
    Represents one MAC address
    """
    def __init__(self, mac):
        self._mac = self.normalize_mac(mac)
        if self._mac is None:
            raise ValueError(1, 'Incorrect MAC address %s' % mac)

    def __str__(self):
        """
        Returns default format, 0102.0304.0506
        """
        return self._mac

    def str_colon(self):
        """
        Returns format with colon delemiter: 01:02:03:04:05:06
        """
        m = self._mac
        return "%s:%s:%s:%s:%s:%s" % (m[0:2], m[2:4], m[4:6], m[6:8], m[8:10], m[10:])

    def normalize_mac(self, mac):
        """
        Check if mac address is ok, and normalize it
        Normalized format: 1122.33aa.bbcc
        Returns None if incorrect

        # Validates that mac-format is in one of following formats:
        # "11:22:33:aa:bb:cc"
        # "11:22:33:AA:BB:CC"
        # "11.22.33.aa.bb.cc"
        # "11.22.33.AA.BB.CC"
        # "11-22-33-aa-bb-cc"
        # "11-22-33-AA-BB-CC"
        # "1122.33aa.bbcc"
        # "1122.33AA.BBCC"
        # "112233aabbcc"
        # "112233AABBCC"
        """
        mac = mac.lower().translate({ ord(c): None for c in ":-. "})
        if len(mac) != 12:
            return None
        try:
            int(mac, 16)
        except ValueError:
            return None

        return "%s.%s.%s" % ( mac[0:4], mac[4:8], mac[8:])

    def add(self, offset):
        mac = re.sub("[^0-9a-fA-F]", "", macAddress)   # strip everything except hex char
        mac = int(mac, 16)  # to integer
        mac += offset
        macAddress = network.format_mac("%012x" % mac)  # to string again


class Peers:
    """
    Represents a number of L2 peers in an 
    Each local interface can handle one remote peer
    """
    def __init__(self):
        self._peers = {}    # key is local interface name
        self._need_sort = False
    
    def _sort(self):
        """
        Sort peers in ascending interface name order
        """
        if self._need_sort:
            self._need_sort = False
        keys = sorted(self._peers.keys())
        tmp = {}
        for key in keys:
            tmp[key] = self._peers[key]
        self._peers = tmp

    def add(self, peer):
        self._peers[peer.local_if] = peer
        self._need_sort = True
    
    def exists(self, peer):
        """
        Returns true if peer exist
        """
        return peer.local_if in self._peers

    def __iter__(self):
        if self._need_sort:
            self._sort()

        for peer in self._peers.values():
            yield peer.local_if, peer


class Peer(AttrDict):
    """
    Represents one L2 peer, usually discover by LLDP, CDP or similar
    """
    # def __init__(self,
    #              local_if=None, 
    #              remote_hostname=None,
    #              remote_mac=None,
    #              remote_if=None, 
    #              remote_ipaddr=None,
    #              remote_description=None):
    #     self.local_if = local_if
    #     self.remote_hostname = remote_hostname
    #     self.remote_mac = remote_mac
    #     self.remote_if = remote_if
    #     self.remote_ipaddr = remote_ipaddr
    #     self.remote_description = remote_description

    def __str__(self):
        return "Peer(local_if '%s', remote_hostname '%s', remote_mac '%s', remote_if '%s', remote_ipaddr '%s', remote_description '%s')" % (\
            self.local_if, 
            self.remote_hostname, 
            self.remote_mac,
            self.remote_if, 
            self.remote_ipaddr, 
            self.remote_description)


class VLAN:
    def __init__(self, id=None, tagged=False, description=None):
        self.id = id
        self.tagged = tagged
        self.description = description

    def __repr__(self):
        return "VLAN(%s)" % self.to_str()

    def __str__(self):
        return str(self.id)

    def to_str(self):
            return "id=%s, tagged=%s, description='%s'" % (self.id, self.tagged, self.description)


class VLANS:
    '''
    Manage a bunch of VLANs, as a dictionary
    '''
    def __init__(self, vlans=None, delemiter=",", range_delemiter="-"):
        super().__init__()
        self._delemiter = delemiter
        self._range_delemiter = range_delemiter
        self._vlans = AttrDict()
        if vlans:
            self.__iadd__(vlans)

    def __add__(self, other):
        """
        Add two VLANS to each other
        """
        if not isinstance(other, VLANS):
            raise TypeError("Error: Can only handle object of VLANS()")
        tmp = self.copy()
        for vlan in other._vlans.values():
            tmp._vlans[vlan.id] = vlan
        return tmp

    def __iadd__(self, other):
        if isinstance(other, VLANS):
            for vlan in other._vlans.values():
                self._vlans[vlan.id] = vlan
        elif isinstance(other, VLAN):
            self._vlans[other.id] = other
        else:
            raise TypeError("Error: Can only handle object of VLANS() or VLAN() got %s" % type(other))
        return self

    def __str__(self):
        return dict_to_vlan_str(self._vlans,
                                delemiter=self._delemiter,
                                range_delemiter=self._range_delemiter)

    def __repr__(self):
        s = ""
        for vlan in self._vlans.values():
            s += "(%s)" % vlan.to_str()
        return "VLANS(%s)" % s

    def __iter__(self):
        return iter(self.__dict__)

    def items(self):
        for item in self._vlans.items():
            yield item

    def keys(self):
        for item in self._vlans.keys():
            yield item
            
    def values(self):
        for item in self._vlans.values():
            yield item



def main():
    pass
    

if __name__ == "__main__":
    main()
