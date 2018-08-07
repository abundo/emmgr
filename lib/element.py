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
    Manage one element. 
    This is a object factory, returns BaseDriver + actual driver
    Manage one element. This is a stub that loads the real driver
    """

    @classmethod
    def get_models(cls):
        res = []
        models = os.listdir(config.driver_dir)
        models = sorted(models)
        for model in models:
            if model[0] != "_" and os.path.isdir(config.driver_dir + os.sep + model):
                res.append(model)
        return res


    def __init__(self, **kwargs):
        hostname = kwargs.get("hostname")
        model = kwargs.get("model")
        ipaddr_mgmt = kwargs.get("ipaddr_mgmt")

        if model is None:
            raise self.ElementException("Element model must be specified")
        
        if ipaddr_mgmt is None:
            # Find out management IP address through DNS
            addr = socket.gethostbyname(hostname)
            kwargs['ipaddr_mgmt'] = addr

        # Copy in some defaults from config, if not specified
        for key, attr in config.em.scriptaccount.items():
            if key not in kwargs:
                kwargs[key] = attr

        definitions = BaseDriver.load_definitions(model)

        # load the element driver for the element model
        driver_file = config.driver_dir + "/%s.py" % definitions[-1].driver
        if not os.path.exists(driver_file):
            raise self.ElementException("Missing element driver %s" % driver_file)
        self._drivermodule = util.import_file(driver_file)

        # Create instance of driver
        kwargs['definitions'] = definitions
        self._driver = self._drivermodule.Driver(**kwargs)
    
    def __getattr__(self, attr):
        """Bridge to the driver specific code"""
        return getattr(self._driver, attr)


def main():
    import emmgr.lib.cli
    emmgr.lib.cli.main(mgr_cls=Element)


if __name__ == '__main__':
    main()
