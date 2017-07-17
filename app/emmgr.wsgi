#!/usr/bin/env python3
import sys, logging
logging.basicConfig(stream=sys.stderr)

sys.path.insert(0, '/opt')
from app import app as application
