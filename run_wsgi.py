#!/usr/bin/env python3

"""
Start a flask development server with full debug.
"""

import sys
import yaml

with open("/etc/emmgr/emmgr.yaml", "r") as f:
    try:
        config = yaml.load(f)
    except yaml.YAMLError as err:
        print("Error: cannot load configuration, aborting. Err: %s" % err)
        sys.exit(1)

sys.path.insert(0, config['basedir'])
from emmgr.app import app

app.run(host='0.0.0.0', port=5101, debug=True)
