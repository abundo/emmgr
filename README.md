# emmgr

# Intro

Emmgr is an application and library for handling network elements, typically routers and switches.

Emmgr contains several modules

* Element manager
    * Library with useful functions
* CLI
    * Gives access to the library from the command line


# Directories overview

| Directory              | Description                 |
| -----------------------| --------------------------- |
| /etc/emmgr             | Configuration directory     |
| /opt/emmgr             | Base directory              |
| /opt/emmgr/cli         | CLI                         |
| /opt/emmgr/config      | Example configuration files |
| /opt/emmgr/drivers     | Element drivers             |
| /opt/emmgr/lib         | Library modules             |


# Installation

Clone the emmgr git repository

    git clone https://github.com/abundo/emmgr.git


Install required modules/libraries

    sudo apt install python3-jinja2
    sudo pip3 install orderedattrdict


Copy the example configuration file. 

    sudo mkdir /etc/emmgr
    sudo cp /opt/emmgr/config/emmgr-example.yaml /etc/emmgr/emmgr.yaml

Edit the configuration file, with correct username, password etc. Available options can be found in the example configuration file. The configuration file uses the YAML format. For more information on YAML see <https://en.wikipedia.org/wiki/YAML>


# Components

## CLI

| Base directory          | Description               |
| ------------------------| ------------------------- |
| /opt/emmgr/cli/emmgr.py | CLI wrapper that gives access to most functions in emmgr |


With this script most functions in emmgr can be called.

To make it easy to access, create an symlink somwhere in your path

    sudo ln -s /opt/emmgr/cli/emmgr /usr/local/lib/emmgr

emmgr CLI uses the first argument to select what module to run.


### Show help

	$ emmgr
	
	Usage:
	    emmgr <module> <parameters>
	
	Available modules:
	    em           Manage elements 
	
	For help on modules, use
	    emmgr <module> -h

For documentation on each module, see module section below.


### Show em help

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


### Run a command and show output (run)

todo

### Fetch running_configuation (get_running_config)

todo

### Save the running configuration to non-volatile storage (save_running_config)

todo


### Show all firmware files (sw_list)

	alr@emmgr:/opt/emmgr$ ./element.py sw_list -H bj1a1 --model asr920
	Softare on element:
	asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	asr920-LUNET_CFD_316_PEGM.bin
	asr920-universalk9_npe.03.16.02a.S.155-3.S2a-ext.bin

### Verify if a firmware exist (sw_exist)

	alr@emmgr:/opt/emmgr$ ./element.py sw_exist -H bj1a1 --model asr920 --filename asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	
	Does firmware asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin exist ?  True

### Copy a firmware file to element (sw_copy_to)

todo

### Configure boot firmware (sw_set_boot)

todo

### Remove a firmware file from element (sw_delete)

todo

### Delete old files (sw_delete_unneeded)

todo

#### Upgrade firmare (sw_upgrade)

todo

----------------------------------------------------------------------

# Use emmgr as a library

Most of the library modules can be directly executed, or be imported and used as libraries by other python scripts.

Note, to be able to use these from CLI, set PYTHONPATH. Example:

	$ export PYTHONPATH=/opt
	$ cd /opt/emmgr/lib
	$ ./element.py
	<output from script>


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

Specific drivers exist for

* Cisco ASR920 (IOS)
* Cisco ME3400 (IOS)
* Cisco C4500 (IOS)
* Huawei S5700 (VRP)
* Waystream MS4000 (iBOS)
* ZTE RS5128 (zxros)



## Show all firmware files (sw_list)

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


## comm.py

Communicates with an element over telnet or ssh. Similar to expect.

Has no functionality when used directly as a script.


## config.py

Reads the emmgr configuration file


## List all files in a element (sw_list)

	alr@emmgr:/opt/emmgr/em$ ./element.py sw_list -H bj1a1 --model asr920
	Softare on element:
	asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	asr920-LUNET_CFD_316_PEGM.bin
	asr920-universalk9_npe.03.16.02a.S.155-3.S2a-ext.bin


## Check if a file exist in a element (sw_exist)

	alr@emmgr:/opt/emmgr/em$ ./element.py sw_exist -H bj1a1 --model asr920 --filename asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	
	Does firmware asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin exist ?  True

## Copy a file to element (sw_copy_to)

todo

## Set firmware to boot (sw_set_boot)

todo

## Delete a file (sw_delete)

todo

## Delete old files (sw_delete_unneeded)

todo

## Upgrade firmare (sw_upgrade)

todo


## util.py

Various help functions.

Has no functionality when used directly as a script.



----------------------------------------------------------------------

# Development

Here are documentation related to development of emmgr and its driver modules


# IDE

The development of emmgr is done using visual studio code with the python extension


##	Create a new element driver

* Drivers are located in /opt/emmgr/drivers
* Each driver has a subdirectory, the name of the subdirectory should have the same name as the element model.
* In the driver directory a yaml configuration file must be created. It specifies things such as
    * What driver to use
    * Which interfaces an element has and their names
    * default firmware
    * filter to filter out firmware files

When creating a new driver, it is easiest to copy an existing and modify this
