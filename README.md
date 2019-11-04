# emmgr

# Intro

Emmgr is an application and library for handling network elements, typically routers and switches.

Emmgr contains several modules

* Element manager
    * Library with useful functions
* CLI
    * Gives access to the library from the command line


Generic drivers exist for

* Cisco IOS
* Cisco SMB (Small Business)
* Huawei VRP
* Waystream iBOS (PacketFront) 
* ZTE zxros

Specific drivers exist for

* Cisco ASR920 (IOS)
* Cisco ME3400 (IOS)
* Cisco C4500 (IOS)
* Huawei S5700 (VRP)
* Waystream MS4000 (iBOS)
* ZTE RS5128 (zxros)



# Directories overview

| Directory              | Description                 |
| -----------------------| --------------------------- |
| /etc/emmgr             | Configuration files         |
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

    sudo ln -s /opt/emmgr/cli/emmgr.py /usr/local/lib/emmgr

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
		get_bootloader
		get_running_config
		interface_clear_config
		interface_get_admin_state
		interface_set_admin_state
		l2_peers
		license_get
		license_set
		list_models
		reload
		run
		save_running_config
		set_bootloader
		set_startup_config
		sw_copy_to
		sw_delete
		sw_delete_unneeded
		sw_exist
		sw_get_boot
		sw_get_version
		sw_list
		sw_set_boot
		sw_upgrade
		vlan_create
		vlan_delete
		vlan_get
		vlan_interface_create
		vlan_interface_delete
		vlan_interface_get
		vlan_interface_set_native

Each command has it's own set of command arguments. To view those:

    $ emmgr em <command> -h

example

    $ emmgr em run -h

	usage: emmgr [-h] [-H HOSTNAME] [-i IPADDR_MGMT] -m MODEL [-u USERNAME]
				[-p PASSWORD] [-e ENABLE_PASSWORD] [-t]
				[--loglevel {info,warning,error,debug}] [--json] -c COMMAND

	optional arguments:
	-h, --help            show this help message and exit
	-H HOSTNAME, --hostname HOSTNAME
							Hostname of element
	-i IPADDR_MGMT, --ipaddr_mgmt IPADDR_MGMT
							Management IP address of element
	-m MODEL, --model MODEL
							Element model
	-u USERNAME, --username USERNAME
							Username for connecting
	-p PASSWORD, --password PASSWORD
							Password for connecting
	-e ENABLE_PASSWORD, --enable_password ENABLE_PASSWORD
							Password for enable mode
	-t, --telnet          Use Telnet
	--loglevel {info,warning,error,debug}
							Set loglevel, one of info, warning, error or debug
	--json                Output result in json format
	-c COMMAND, --command COMMAND
							Command to run


### Configure element (configure)

todo

### Get current bootloader (get_bootloader)

todo


### Get the running configuation (get_running_config)

	$ emmgr em get_running_config -m ibos -H cb8w2
	! version ibos-ms4k-7.3.5-ED-RC2 (ibos-ms4k-7.3.5-ED-RC2.bz2)
	interface vlan212
	<rest of output not shown here>


### Clear all configuration on an interface (interface_clear_config)

todo


### Get administrative state on an interface (interface_get_admin_state)

todo


### Set admninistrative state on an interface (interface_set_admin_state)

todo


### Get layer2 peers (l2_peers)

todo


### Get license (get_license)

todo


### Set license (set_license)

todo


### List supported models (list_models)

todo


### Reload element (reload)

todo


### Run a command and show output (run)

	$ emmgr em run -m ibos -c 'show version' -H cb8w2
	Intelligent Broadband Operating System (iBOS), Version 7.3.5-ED-RC2
	<rest of output not shown here>


### Save the running configuration to non-volatile storage (save_running_config)

	$ emmgr em save_running_config -m ibos -H cb8w2 | more
	Result : True


### Set bootloader to use (set_bootloader)

todo


### Set startup configuration (set_startup_config)

todo


### Copy a firmware file to element (sw_copy_to)

todo


### Remove a firmware file from element (sw_delete)

todo


### Delete old files (sw_delete_unneeded)

todo


### Verify if a firmware exist (sw_exist)

	$ emmgr em sw_exist -H bs3a1 --model asr920 --filename asr920-universalk9_npe.16.12.01.SPA.bin
    Does firmware asr920-universalk9_npe.16.12.01.SPA.bin exist ?  True


### Get bootloader (sw_get_boot)

todo



### Get version on running firmware (sw_get_version)

todo


### Show all firmware files (sw_list)

	$ emmgr em sw_list -H bs3a1 --model asr920
	Softare on element:
		asr920-universalk9_npe.16.12.01.SPA.bin
		asr920-universalk9_npe.03.18.03.SP.156-2.SP3-ext.bin


### Configure boot firmware (sw_set_boot)

todo


#### Upgrade firmare (sw_upgrade)

todo


### Create a VLAN (vlan_create)

todo


### Delete a VLAN (vlan_delete)

todo


### Get info on a VLAN (vlan_get)

todo


### Add a VLAN on an interface (vlan_interface_create)

Todo


### Delete a VLAN from an interface (vlan_interface_delete)

Todo


### Get all VLANs on an interface (vlan_interface_get)

Todo


### Set native VLAN on an interface (vlan_interface_set_native)

Todo


----------------------------------------------------------------------

# Library functions

All the above commands can also be used from Python.

Note, to be able to use these from Python, set PYTHONPATH. emmgr loads drivers etc dynamically,
without the PYTHONPATH it will not find them.

Example:

	$ export PYTHONPATH=/opt


## Element manager


| Path                  | Description               |
| ----------------------| ------------------------- |
| /opt/emmgr/element.py | A generic module for doing element management |


element.py can be executed directly as a script (mostly used during development), or imported from other code and user as a library.

element.py is using a generic class and drivers for vendor specific communication. Each driver has its own configuration file.

Available methods:

### Configure element (configure)

todo

### Get current bootloader (get_bootloader)

todo


### Get the running configuation (get_running_config)

todo

### Clear all configuration on an interface (interface_clear_config)

todo


### Get administrative state on an interface (interface_get_admin_state)

todo


### Set admninistrative state on an interface (interface_set_admin_state)

todo


### Get layer2 peers (l2_peers)

todo


### Get license (get_license)

todo


### Set license (set_license)

todo


### List supported models (list_models)

todo


### Reload element (reload)

todo


### Run a command and show output (run)

todo


### Save the running configuration to non-volatile storage (save_running_config)

todo


### Set bootloader to use (set_bootloader)

todo


### Set startup configuration (set_startup_config)

todo


### Copy a firmware file to element (sw_copy_to)

todo


### Remove a firmware file from element (sw_delete)

todo


### Delete old files (sw_delete_unneeded)

todo


### Verify if a firmware exist (sw_exist)

todo


### Get bootloader (sw_get_boot)

todo


### Get version on running firmware (sw_get_version)

todo


### Show all firmware files (sw_list)

Contents of sw_list.py

    #!/usr/bin/env python3
    
    import emmgr.lib.element as element

	# Create an instance (loads drivers etc)
    e = element.Element(hostname=”bj1a1”, model=”asr920”)

	# Execute method and show result
    for sw in e.sw_list():
        print(sw)


Output when run

	$ ./sw_list.py
	asr920-universalk9_npe.03.18.01.S.156-2.S1-std.bin
	asr920-LUNET_CFD_316_PEGM.bin
	asr920-universalk9_npe.03.16.02a.S.155-3.S2a-ext.bin


### Configure boot firmware (sw_set_boot)

todo


#### Upgrade firmare (sw_upgrade)

todo


### Create a VLAN (vlan_create)

todo


### Delete a VLAN (vlan_delete)

todo


### Get info on a VLAN (vlan_get)

todo


### Add a VLAN on an interface (vlan_interface_create)

Todo


### Delete a VLAN from an interface (vlan_interface_delete)

Todo


### Get all VLANs on an interface (vlan_interface_get)

Todo


### Set native VLAN on an interface (vlan_interface_set_native)

Todo



### Show all firmware files (sw_list)

Todo


## basedriver.py


| Path                   | Description               |
| ---------------------- | ------------------------- |
| /opt/emmgr/lib/basedriver.py | Base functionality for all drivers |


## cli.py

| Path                   | Description               |
| ---------------------- | ------------------------- |
| /opt/emmgr/lib/cli.py  | CLI definition for drivers and emmgr command |

The CLI is defined in this file, and used by all drivers, the emmgr em command


## comm.py

| Path                   | Description               |
| -----------------------| ------------------------- |
| /opt/emmgr/lib/comm.py | Communicates with an element over telnet or ssh. Similar to expect |


## config.py

| Path                      | Description               |
| --------------------------| ------------------------- |
| /opt/emmgr/lib/config.py  | Reads the emmgr configuration file |

Has no functionality when used directly as a script.


## emtypes.py

| Path                      | Description               |
| --------------------------| ------------------------- |
| /opt/emmgr/lib/emtypes.py | Defines high level data types |

Here are classes that define
- MAC_Address
- VLAN, VLANs
- Peers, Peer (L2 connectivity)

Has no functionality when used directly as a script.


## log.py

| Path                      | Description               |
| --------------------------| ------------------------- |
| /opt/emmgr/lib/log.py     | Used for logging, default syslog |

Has no functionality when used directly as a script.


## util.py

| Path                     | Description               |
| -------------------------| ------------------------- |
| /opt/emmgr/lib/util.py   | Various help functions |

Has no functionality when used directly as a script.



----------------------------------------------------------------------

# Development

Here are documentation related to development of emmgr and its driver modules

Todo


## IDE

The development of emmgr is done using visual studio code with the python extension


##	Create a new element driver

* Drivers are located in /opt/emmgr/drivers
* Each driver has a subdirectory, the name of the subdirectory should have the same name as the element model.
* In the driver directory a yaml configuration file must be created. It specifies things such as
    * What driver to use
    * Which interfaces an element has and their names
    * default firmware
    * filter to filter out firmware files

When creating a new driver, it is easiest to copy an existing and modify it.
