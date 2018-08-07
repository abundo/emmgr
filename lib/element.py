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


class Element:
    """
    Manage one element. This is a stub that loads the real driver
    """

    ElementException = BaseDriver.ElementException  # for easy access

    @classmethod
    def get_models(cls):
        res = []
        models = os.listdir(config.driver_dir)
        models = sorted(models)
        for model in models:
            if model[0] != "_" and os.path.isdir(config.driver_dir + os.sep + model):
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
        driver_file = config.driver_dir + "/%s.py" % definitions[-1].driver
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


def main():
    import emmgr.lib.cli
    emmgr.lib.cli.main(mgr_cls=Element)


if __name__ == '__main__':
    main()
