# TPMP
**Thermo-regulated Power Management Platform** software is a Python interface to control a platform's temperature, using a Peltier module.

Main interfaces are:
* basicSerialAuto.py: an interactive (terminal like) interface to control TPMP and issue commands "manually"
* testlauncher.py: a fully automated framework that allows to launch a test suite and collect results based on a configuration file

Requirements
## Environment:
python3 is supported  
python2 is no longer tested


### Requirements:

* Python2 (deprecated):
~~~~
sudo apt-get install python-serial
sudo pip install configparser
~~~~

* Python3:
~~~~
sudo apt-get install python3-serial
sudo apt-get install python3-pip
sudo pip3 install PyCRC
sudo pip3 install configparser
~~~~

References:
* [Pyserial](http://pyserial.readthedocs.io/en/latest/shortintro.html)
* [Serial port programming](https://elinux.org/Serial_port_programming)
* [Serial port communication](https://tungweilin.wordpress.com/2015/01/04/python-serial-port-communication/)

### External Library:

Python Library to interface with Meerstetter TEC is not provided.

An example implementation is provided here as reference: `tpmp-ctrl/python/lib/meerstetter`

## Content:

    ├── AUTHORS  
    ├── boardConf: Examples of configuration files for different boards/setup  
    │   └── NXP  
    │       └── imx8  
    │           ├── 845noTB_config.ini: no TB for no Thermo-regulation bench  
    │           ├── basic_850.ini: Interfactive mode, automation not used   
    │           ├── basic_imxqXP.ini: Interfactive mode, automation not used   
    │           ├── launcher850_25C.ini: automation mode  
    │           └── launcher850_50C.ini  
    ├── LICENSE  
    ├── python  
    │   ├── basicSerialAuto.py: Use this script for interactive TPMP commands ie: set the Die temperature On 
    thermal Bench  
    │   ├── default_config.ini: Default conf file for basicSerialAuto.py to be customized  
    │   ├── escapesh.py  
    │   ├── launcher_default_config.ini: Default conf file for testlauncher.py to be customized  
    │   ├── launcher_M845S_config.ini    
    │   ├── lib  
    │   │   ├── __init__.py  
    │   │   ├── meerstetter: Interface for TEC-1091, pyMeCom can be copied here, instructions in README  
    │   │   │   ├── README.md  
    │   │   │   └── tempcontrol.py: utils for Peltier control interface  
    │   │   ├── serial  
    │   │   │   └── connectSerialPort.py: utils for serial port  
    │   │   └── utils  
    │   │       ├── boardInit.py: pwrcycle and reboot sequences  
    │   │       ├── confFile.py: read write conf file  
    │   │       ├── fileOp.py: Operations on files through serial port   
    │   │       ├── __init__.py  
    │   │       ├── peltierOp.py: wrapper for Peltier  
    │   │       └── sendMailConf.py: send results  
    │   ├── minitermcust.py: alternative to basicSerialAuto.py. Deprecated. (not compatible with testlauncher)  
    │   └── testlauncher.py: TPMP Automated Framework   
    ├── README.md  
    ├── shell: shell scripts optionally pushed on board at boot time  
    │   ├── M845S  
    │   │   ├── ... test list related to M845S project  
    │   ├── M850D  
    │   │   ├── ... test list related to M850D project  
    │   ├── print_temp1min.sh  
    │   ├── print_temp.sh  
    │   ├── print_temp_time_s.sh  
    │   └── UTILS: generic shell for re-use in projects   
    │       ├── armClkDiv2.sh  
    │       ├── changehostname.sh  
    │       ├── config.sh  
    │       ├── OFFLineCPU123.sh  
    │       ├── OPP-setup.sh  
    │       ├── print_temp1min.sh  
    │       ├── print_temp.sh  
    │       ├── print_temp_time_s.sh  
    │       ├── setUsrGov1Ghz.sh  
    │       ├── suspend.sh  
    │       └── wifiEnable.sh  
    ├── TECServiceWinConf: Files for windows GUI TEC Service v3.00  
    │   └── ConfigThermalBenchFinal.ini: Configuration for this prototype  
    ├── tools: post processing tools examples  
    │   ├── parse: result refactorization  
    │   │   ├── czparse845xl.py  
    │   │   ├── czparse845xlunity.py  
    │   │   ├── czparsexl_legacy.py  
    │   │   └── czparsexl.py  
    │   └── plot: results plotting  
    │       ├── allpwrfilter.plot  
    │       ├── allpwrraw.plot  
    │       ├── reportfull.plot  
    │       └── reportPower.plot  
    └── uboot: Additional uboot instruction launched at boot time (optional)  
        ├── ubootcfg_1600DDR.txt  
        ├── ubootcfg_oldboard.txt  
        └── ubootcfg.txt  


## basicSerialAuto.py Quick start guide:


### START Method1 EVK has already been started:

#### step0: prerequesite
EVK has already been started and connected through serial port (ie: picocom -b 115200 /dev/ttyUSB0)
Login has been entered (ie: enter Login: root)
#### step1:
~~~~
cd tpmp_ctrl/python/
python3 basicSerialAuto.py
~~~~

~~~~
>---  1: /dev/ttyUSB0         'CP2105 Dual USB to UART Bridge Controller'
> 'USB VID:PID=10C4:EA70 SER=007FD572 LOCATION=3-6'
>---  2: /dev/ttyUSB1         'CP2105 Dual USB to UART Bridge Controller'
> 'USB VID:PID=10C4:EA70 SER=007FD572 LOCATION=3-6'
>identify port by hwid:/dev/ttyUSB0
>/dev/ttyUSB0 is open...
>Peltier hwid initialized with : 0403:6015
>Initialise
>Enter command or 'exit':

Script connected thanks to default_config.ini config file waiting for commands
~~~~

#### step2:
`cmdlist`  
>commands  
>-- cmdlist: Displays this help  
>-- help: regular shell help  
>-- exit to quit  
>-- pole to get pack to polling mode  
>-- shell commands to keep stay in interactive mode  
>-- console to configure serial Output ON/OFF for debug  
>-- cpfile to copy txt file from host to target current dir  
>-- cpexec to copy binary file from host to target current dir  
>-- cpdir to copy entire dir from host to current dir  
>-- peltier to set temp for Peltier setup and wait for stabilization  
>-- peltierImmediate to set temp for Peltier setup wo wait time  
>-- readPeltier to read current Peltier Object temperature  
>-- dietemp to set temp for die adjusted automatically through peltier  
>-- readDieTemp to read die temp  
>-- rzmodem to copy file from host to target  
>-- szmodem to copy file from target to host  
>-- autocomplete to enable autocompletion when not activated by default  
>-- pwrcycle to shut down pwr through acme then pwron and bootup  


#### step3:
`dietemp`
>Enter Die temp Target
`60`

System will converge to 60°C then get back to Enter command or 'exit' when finished with last message:
>Die temp target reached
>Peltier temp: 58, DieTemp:  60, deltaPeltierDie: 2

### START Method2 use script to startup the board:

#### step1: power up board
#### step2: launch thermal bench script:  
~~~~
cd tpmp_ctrl/python/
python3 basicSerialAuto.py
~~~~
it's expected to hang here  
#### step3:  
Put script in polling mode  
>Enter command or 'exit':  
`pole`  
chose polling timeout in seconds here 60sec  
>Enter polling timeout:  
`60`  
Script is preparing the board  
Return to polling timeout set to:60  
#### step4:   
Reset EVK by triggering reset button (or power OFF/ON cycle)  
>UBOOT print identified  
>--- Sending file ../uboot/ubootcfg.txt ---  
>--- Commands from File ../uboot/ubootcfg.txt sent ---  
>catch enter password to login   
>--- Sending file ../tmp_shell/print_temp_time_s.sh ---  
>...............  
>--- File ../tmp_shell/print_temp_time_s.sh sent ---  
>--- Sending file ../tmp_shell/print_temp1min.sh ---  
>..........  
>--- File ../tmp_shell/print_temp1min.sh sent ---  
>--- Sending file ../tmp_shell/print_temp.sh ---  
>......  
>--- File ../tmp_shell/print_temp.sh sent ---  
>Board Connection pattern identified  
>BOARD INIT COMPLETED  


### CUSTOM conf file:

You can create your own configuration file instead of using default default_config.ini
To launch custom config file custom_config.ini:  
~~~~
cd tpmp_cytl/python/  
python3 basicSerialAuto.py custom_config.ini  
~~~~

To create a new config file, you can either copy and rename existing config file then modify. If you want to start from empty config file, you can just launch:  
`python3 basicSerialAuto.py myNewConfig.ini`    
This will fill-up the Config file on the fly (under development not recomended)

## testlauncher.py Quick start guide:
### Configuration
1. No configuration file available for this board  
	* Create your own based on `tpmp_ctrl/launcher_default_config.ini`  
	* Launch with `python3 testlauncher.py myconfig.ini`  
1. Configuration file available for this board  
	* Adjust your parameters  
	* Launch with `python3 testlauncher.py myconfig.ini`  


