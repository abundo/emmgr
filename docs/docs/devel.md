# Development

Here are documentation related to development of emmgr and its driver modules


----------------------------------------------------------------------

# Overview

Filesystem

| Directory              | Description               |
| -----------------------| ------------------------- |
| /opt/emmgr             | Base directory            |                
| /opt/emmgr/apache2     | Apache2 config file       |
| /opt/emmgr/app         | GUI Webapp                |
| /opt/emmgr/cli         | CLI                       |
| /opt/emmgr/config      | Example configuration files | 
| /opt/emmgr/docs        | Source of documentation   |
| /opt/emmgr/drivers     | Element drivers           |
| /opt/emmgr/lib         | Library modules           |


# Documentation

Documentation is written in markdown, and webpages are created by mkdoc.

Apache is configured so documentation is handled as static pages, so they are not processed by python/flask.

When documentation is changed, rebuild the webpages:

    cd /opt/emmgr/docs
    mkdocs rebuild


# Installation

The development of emmgr is done using
* eclipse with extensions
    * pydev, python module for eclipse
    * yaml, module for eclipse
