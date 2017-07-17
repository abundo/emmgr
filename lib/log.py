#!/usr/bin/env python3

'''
Logging functionality
'''

import sys
import logging
import logging.handlers

INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
DEBUG = logging.DEBUG

level_dict = {'info': logging.INFO, 
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'debug': logging.DEBUG}
    
def activateSyslog():
    syslogger = logging.handlers.SysLogHandler(address='/dev/log')

    formatter = logging.Formatter('%(module)s [%(process)d]: %(levelname)s %(message)s')
    syslogger.setFormatter(formatter)
    logger.addHandler(syslogger)

def setLevel(level):
    if isinstance(level, str):
        level = level_dict[level]
    logger.setLevel(level)

def info(msg):
    msg = str(msg).replace('\n', ', ')
    logger.info(msg)

def warning(msg):
    msg = str(msg).replace('\n', ', ')
    logger.warning(msg)

def error(msg):
    msg = str(msg).replace('\n', ', ')
    logger.error(msg)

def debug(msg):
    try:
        msg = str(msg).replace('\n', ', ')
    except UnicodeDecodeError:
        return
    logger.debug(msg)

def log(level, msg):
    try:
        msg = str(msg).replace('\n', ', ')
    except UnicodeDecodeError:
        return
    logger.log(level, msg)

def addLogger(stream):
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return handler

def removeLogger(handler):
    logger.removeHandler(handler)

formatstr='%(asctime)s %(levelname)s %(message)s '
loglevel = logging.INFO
logger = logging.getLogger('luconf')
logger.setLevel(loglevel)

# remove all handlers
for hdlr in logger.handlers:
    logger.removeHandler(hdlr)

consolehandler = logging.StreamHandler()
# consolehandler.setLevel(loglevel)

formatter = logging.Formatter(formatstr)
consolehandler.setFormatter(formatter)
logger.addHandler(consolehandler)
