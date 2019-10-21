#!/usr/bin/env python
#
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Utils for serial port connection

import sys
import re
import serial
from serial.tools.list_ports import comports


def get_serial_port_by_hwid(hwid):
    ports = []
    for n, (port, desc, hwid) in enumerate(sorted(serial.tools.list_ports.grep(hwid)), 1):
        sys.stderr.write('--- {:2}: {:20} {!r}\n {!r}\n'.format(n, port, desc, hwid))
        ports.append(port)
    return ports

def get_serial_hwid_by_port(port):
    for n, (port, desc, hwid) in enumerate(sorted(serial.tools.list_ports.grep(port)), 1):
        sys.stderr.write('--- {:2}: {:20} {!r}\n {!r}\n'.format(n, port, desc, hwid))
        searchRes = re.search( r'.*PID=(.*?) .*', hwid)

    return searchRes.group(1)

def get_port_from_key (ports):
    while True:
        #port = raw_input('--- Enter port index or full name: ') deprecated in py3
        port = input('--- Enter port index or full name: ')
        try:
            index = int(port) - 1
            if not 0 <= index < len(ports):
                sys.stderr.write('--- Invalid index!\n')
                continue
        except ValueError:
            pass
        else:
            port = ports[index]
        print("get_port_from_key:" + str(port))
        return port

def get_port_from_conf (ports,serial_port):
    port = ports[int(serial_port) - 1]
    print("get_port_from_conf:" + str(port))
    return port

def ask_for_port():
    """
    Show a list of ports and ask the user for a choice. To make selection
    easier on systems with long device names, also allow the input of an
    index.
    """
    sys.stderr.write('\n--- Available ports:\n')
    ports = []
    for n, (port, desc, hwid) in enumerate(sorted(serial.tools.list_ports.comports()), 1):
        sys.stderr.write('--- {:2}: {:20} {!r}\n {!r}\n'.format(n, port, desc, hwid))
        ports.append(port)
    while True:
        port = input('--- Enter port index or full name: ')
        try:
            index = int(port) - 1 #FSY: change code for readability in case of 'full name'
            if not 0 <= index < len(ports):
                sys.stderr.write('--- Invalid index!\n')
                continue
        except ValueError:
            pass
        else:
            port = ports[index] #FSY: cleanup...
        return port

def get_serial_port(serial_hwid = "UNKNOWN"):
    ports = get_serial_port_by_hwid(serial_hwid)
    if (len(ports) > 0):
        port = ports[0]
        print("identify port by hwid:" + port)
    else:
        port = ask_for_port()
    return port

def connect_serial(serial_hwid = "UNKNOWN", baud = 115200, serial_port = "0"):
    ports = get_serial_port_by_hwid(serial_hwid)
    if (len(ports) == 1):
        port = ports[0]
        print("identify port by hwid:" + port)
    elif (len(ports) > 1):
        print("connect_serial " + str(len(ports)) + " ports with this hwid:")
        if serial_port == "0":
            port = get_port_from_key (ports)
        else:
            port = get_port_from_conf (ports,serial_port)
    else:
        port = ask_for_port()
    return serial.Serial(port, baud, timeout=1)

