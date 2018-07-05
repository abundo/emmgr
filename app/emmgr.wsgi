#!/usr/bin/env python3
import sys, logging
logging.basicConfig(stream=sys.stderr)

sys.path.insert(0, '/opt')
from emmgr.app import app as application
