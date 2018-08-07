#!/usr/bin/env python3
'''
Common utilities
'''

import sys
import os.path
import datetime
import json
import yaml
import pprint
import importlib.machinery
from orderedattrdict import AttrDict

pp = pprint.PrettyPrinter(indent=4)


class UtilException(Exception):
    pass


def die(msg, exitcode=1):
    print(msg)
    sys.exit(exitcode)
    

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return obj.to_dict()


def json_dumps(data):
    return json.dumps(data, default=json_serial)

class AddSysPath:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.savedPath = sys.path.copy()
        sys.path.insert(0, self.path)

    def __exit__(self, typ, value, tb):
        sys.path = self.savedPath

def import_file(pythonFile):
    dir_name = os.path.dirname(pythonFile)
    module_name = os.path.basename(pythonFile)
    module_name = os.path.splitext(module_name)[0]
    loader = importlib.machinery.SourceFileLoader(module_name, pythonFile)
    with AddSysPath(dir_name):
        return loader.load_module()

def get_param(request, params):
    query = AttrDict()
    for param in params:
        query[param] = request.values.get(param, "")
    return query

def pretty_print(msg, d):
    if not isinstance(d, (dict, list)):
        try:
            d = vars(d)
        except TypeError:
            pass
    if msg:
        print(msg)
    pp.pprint(d)

def now():
    return datetime.datetime.now().replace(microsecond=0)

def now_str():
    return now().strftime("%Y%m%d%H%M%S")

def to_int(s):
    try:
        return int(s)
    except ValueError:
        return None

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=AttrDict):
    """
    Load Yaml document, replace all hashes/mappings with AttrDict
    """
    class Ordered_Loader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    Ordered_Loader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, Ordered_Loader)

def yaml_load(filename):
    with open(filename, "r") as f:
        try:
            # self.default_data = yaml.load(f)
            data = ordered_load(f, yaml.SafeLoader)
            return data
        except yaml.YAMLError as err:
            raise UtilException("Cannot load YAML file %s, err: %s" % (filename, err))


class BaseCLI:
    
    def __init__(self):
        import argparse
        self.parser = argparse.ArgumentParser()
        self.add_arguments()
        self.args = self.parser.parse_args()
        
    def add_arguments(self):
        """Superclass overrides this to add additional arguments"""

    def run(self):
        raise ValueError("You must override the run() method")


class Execute_CLI:
    """
    Walk through a module, extract all CLIs and run one of them
    """
    def __init__(self, module_name=None, **kwargs):
        # get all CLI definitions
        self.cmds = AttrDict()
        cli_module = sys.modules[module_name]
        for key in dir(cli_module):
            if key.startswith("CLI_"):
                cls = getattr(cli_module, key)
                self.cmds[key[4:]] = cls
    
        # get first arg, use as command
        if len(sys.argv) < 2:
            self.usage("No command specified, choose one of:")
        
        cmd = sys.argv.pop(1)
        if not cmd in self.cmds:
            self.usage("Unknown command '%s'" % cmd)
    
        obj = self.cmds[cmd](**kwargs)
        obj.run()
        

    def usage(self, msg):
        if msg: 
            print(msg)
        for cmd in self.cmds:
            print("   ", cmd)
        sys.exit(1)


def main():
    print("now()", now())
    print("now_str()", now_str())
    

if __name__ == "__main__":
    main()
