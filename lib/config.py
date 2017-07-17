#!/usr/bin/env python3
'''
Handle configuration data
'''

import sys
import yaml

import emmgr.lib.util as util

# load config file
conf = util.yaml_load("/etc/emmgr/emmgr.yaml")

# Copy loaded config to module globals, for easy access
thismodule = sys.modules[__name__]
for attr, value in conf.items():
    setattr(thismodule, attr, value)
    

def main():
    util.pretty_print("Configuration", conf)


if __name__ == "__main__":
    main()
