# Intro

This document contains a description over emmgr

Emmgr is an application and library for handling network elements, typically routers and switches.

Emmgr contains several modules

* Element manager
    * Library with useful functions
* Webb GUI
    * Can be used for basic element management
* REST API
    * Most of Emmgr functionality can be used via this API
* CLI


# Installation

Clone the emmgr git repository

Install required modules/libraries

    sudo pip3 install orderedattrdict


# Configuration

All configuration is using the YAML format. For more information on YANG see <https://en.wikipedia.org/wiki/YAML>

### Files

Emmgr has one configuration file.

| File                  | Description              |
|-----------------------| -------------------------|
| /etc/emmgr/emmgr.yaml | Main configuration file  |



# Components

## Element manager

| Base directory        | Description               |
| ----------------------| ------------------------- |
| /opt/emmgr/element.py | A generic module for doing element management |

element.py can be executed directly as a script, or imported from other code and user as a library.

element.py is using a generic class and drivers for vendor specific communication. Each driver has its own configuration file.

Generic drivers exist for

* Cisco IOS
* Huawei VRP
* Waystream (PacketFront) iBOS
* ZTE zxros

Specific drivers exist fo

* Cisco ASR920 (IOS)
* Cisco ME3400 (IOS)
* Cisco C4500 (IOS)
* Cisco C6880 (IOS)
* HP A-5500 (todo)
* Huawei S5700 (VRP)
* Waystream MS4000 (iBOS)
* ZTE 5128


### CLI


#### Show help

	$ emmgr 
	
	Usage:
	    emmgr <module> <parameters>
	
	Available modules:
	    em           Manage elements 
	
	For help on modules, use
	    emmgr <module> -h


#### Show em help

	$ emmgr em
	
	No command specified, choose one of:
	    configure
	    get_running_config
	    interface_clear_config
	    list_models
	    reload
	    run
	    save_running_config
	    sw_copy_to
	    sw_delete
	    sw_delete_unneeded
	    sw_exist
	    sw_list
	    sw_set_boot
	    sw_upgrade


#### Run a command and show output (run)

todo

#### Fetch running_configuation (get_running_config)

todo

#### Save the running configuration to non-volatile storage (save_running_config)

todo


#### Show all firmware files (sw_list)

	alr@emmgr:/opt/emmgr$ ./element.py sw_list -H bj1a1 --model asr920
	Softare on element:
	asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	asr920-LUNET_CFD_316_PEGM.bin
	asr920-universalk9_npe.03.16.02a.S.155-3.S2a-ext.bin

#### Verify if a firmware exist (sw_exist)

	alr@emmgr:/opt/emmgr$ ./element.py sw_exist -H bj1a1 --model asr920 --filename asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	
	Does firmware asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin exist ?  True

#### Copy a firmware file to element (sw_copy_to)

todo

#### Configure boot firmware (sw_set_boot)

todo

#### Remove a firmware file from element (sw_delete)

todo

#### Radera gamla filer (sw_delete_unneeded)

todo

#### Upgrade firmare (sw_upgrade)

todo

### Use emmgr as a library

todo

#### Show all firmware files (sw_list)

Contents of sw_list.py

    #!/usr/bin/env python3
    
    import element
    e = element.Element(hostname=”bj1a1”, model=”asr920”)
    for sw in e.sw_list():
        print(sw)
	        
	$ ./sw_list.py
	asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	asr920-LUNET_CFD_316_PEGM.bin
	asr920-universalk9_npe.03.16.02a.S.155-3.S2a-ext.bin


###	Create a new element driver

Drivers are located in /opt/emmgr/drivers
Each driver has a subdirectory, the name of the subdirectory should have the same name as the element model.
In the driver directory a yaml configuration file must be created. It specifies things such as
* What driver to use
* Which interfaces an element has and their names
* default firmware
* filter to filter out firmware files

When creating a new driver, it is easiest to copy an existing and modify this


## emmgr CLI

| Base directory          | Description               |
| ------------------------| ------------------------- |
| /opt/emmgr/cli/emmgr.py | CLI wrapper that gives access to most functions in emmgr |


With this script most functions in emmgr can be called.

To make it easy to access, create an symlink 

    sudo ln -s /opt/emmgr/cli/emmgr /usr/local/lib/emmgr

emmgr CLI uses the first argument to select what module to run.


### Show help

	alr@emmgr:~$ emmgr
	
	Usage:
	    emmgr <module> <parameters>
	
	Available modules:
	    em           Manage network elements 
	
	For help on modules, use
	    emmgr <module> -h

For documentation on each module, see module section below.


## Webb GUI, REST API

| Base directory         | Description               |
| -----------------------| ------------------------- |
| /opt/emmgr/app         |                           |


Graphical GUI to manqage elements.

Uses 
- python flask as framework.
- Uses bootstrap3 to get a good looking responsive design on web pages.

The Web GUI is built according to MVC – Model View Controller.

All HTTP requersts is received by modules in /opt/emmgr/app/controller

Depending on what needs to be done, views are included and shown from /opt/emmgr/app/views

Implements an REST API, which gives access to most functions in emmgr. This is a controller in /opt/emmgr/webapi/controller/api.py


# Modules

| Base directory           | Description               |
| -------------------------| ------------------------- |
| /opt/emmgr/lib           |                           |


Library functions, for the rest of emmgr. Each library module can be directly executed, or be imported and used as libraries by other python scripts.

Note, to be able to use these from CLI, set PYTHONPATH. Example:

	$ export PYTHONPATH=/opt
	$ cd /opt/emmgr/lib
	$ ./comm.py
	<Long output from script>


## comm.py

Communicates with an element over telnet or ssh. Similar to expect.

Has no functionality when used directly as a script.


## config.py

Reads the configuration file


## Hämta ett element och visa info (get)

todo

## Skapa ett element (create)

todo

## Flytta ett element (move)

todo

## Radera ett element (delete)

todo

## Hämta interface roll (get_interface_role)

todo

## Sätt interface roll (set_interface_role)

todo

## Skapa installationsjobb (create_install_job)

todo

## Skapa konfigurationsfil (render)

todo

## Hämta output från ett kommando (get_command_output)

todo

## Hämta aktuell konfiguration (get_running_config)

todo


## Lista alla filer i ett element (sw_list)

	alr@emmgr:/opt/emmgr/em$ ./element.py sw_list -H bj1a1 --model asr920
	Softare on element:
	asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	asr920-LUNET_CFD_316_PEGM.bin
	asr920-universalk9_npe.03.16.02a.S.155-3.S2a-ext.bin


## Kontrollera om en fil finns på element (sw_exist)

	alr@emmgr:/opt/emmgr/em$ ./element.py sw_exist -H bj1a1 --model asr920 --filename asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	
	Does firmware asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin exist ?  True

## Kopiera en fil till element (sw_copy_to)

todo

## Sätt vilken firmware som ska bootas med (sw_set_boot)

todo

## Radera en fil på element (sw_delete)

todo

## Radera gamla filer (sw_delete_unneeded)

todo

## Uppgradera firmare (sw_upgrade)

todo


## util.py

Various help functions.

Has no functionality when used directly as a script.
