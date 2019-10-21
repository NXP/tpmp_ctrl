#!/usr/bin/env python3
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Authors: Jerome NEANNE, Florian Sylvestre
# Mail: jerome.neanne@nxp.com, florian.sylvestre@nxp.com
# description: Implements functions to interface TPMP with PyMeCom lib
"""

"""
import logging
import time
import sys
from serial import SerialException
sys.path.insert(0, '../../')
from lib.serial import connectSerialPort
from lib.utils import confFile
from lib.meerstetter.pyMeCom.mecom import MeCom, ResponseException, WrongChecksum

serial_hwid_default = "UNKNOWN"

# syntax
# { display_name: [parameter_id, unit], }
QUERIES_TABLE = {
    "loop status": [1200, ""],
    "object temperature": [1000, "degC"],
    "target object temperature": [1010, "degC"],
    "output current": [1020, "A"],
    "output voltage": [1021, "V"],
    "sink temperature": [1001, "degC"],
}

class Peltier(object):
    def __init__(self, port):
        self.port = port
        self.mc_session = MeCom(self.port)

    def _tearDown(self):
        self.mc_session.stop()

    def __get_param(self, param_id):
        try:
            value = self.mc_session.get_parameter(parameter_id=param_id, address=self.mc_session.identify())
        except (ResponseException, WrongChecksum) as ex:
            self.mc_session.stop()
            self._session = MeCom(serialport=self.port)
        return value

    def __set_param(self, param_id, param_value):
        try:
            self.mc_session.set_parameter(parameter_id=param_id,
                                          value=param_value,
                                          address=self.mc_session.identify(),
                                          parameter_instance=1)
        except (ResponseException, WrongChecksum) as ex:
            self.mc_session.stop()
            self._session = MeCom(serialport=self.port)

    def display_data(self):
	    data = {}
	    for description in QUERIES_TABLE:
	        data[description] = (self.__get_param(QUERIES_TABLE[description][0]),
                                 QUERIES_TABLE[description][1])
	    print(data)

    def set_temp(self, tempTarget):
        self.__set_param(3000, float(tempTarget))

    def get_temp(self):
        return self.__get_param(1000)

    def is_stable(self):
        return self.__get_param(1200)


def setPeltierTempImmediate(serial_hwid, tempTarget, configFile = "UNKNOWNconfFile.ini"):
    #port = connectSerialPort.connect_serial(serial_hwid)
    port = connectSerialPort.get_serial_port(serial_hwid)
    if serial_hwid  == serial_hwid_default:
        serial_hwid = connectSerialPort.get_serial_hwid_by_port(port)
        print("peltier_serial_hwid = " + serial_hwid)
        confFile.update(configFile, "TEMPBENCH", "peltier_serial_hwid", serial_hwid)
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")
    # initialize controller
    print(port)
    mc = Peltier(port)

    # get the values from DEFAULT_QUERIES
    mc.display_data()
    ret = mc.set_temp(tempTarget)

    return ret

def setPeltierTemp(serial_hwid, tempTarget, configFile = "UNKNOWNconfFile.ini"):
    #port = connectSerialPort.connect_serial(serial_hwid)
    port = connectSerialPort.get_serial_port(serial_hwid)
    if serial_hwid  == serial_hwid_default:
        serial_hwid = connectSerialPort.get_serial_hwid_by_port(port)
        print("peltier_serial_hwid = " + serial_hwid)
        confFile.update(configFile, "TEMPBENCH", "peltier_serial_hwid", serial_hwid)
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")
    # initialize controller
    print(port)
    mc = Peltier(port)

    # get the values from DEFAULT_QUERIES
    print(mc.display_data())
    ret = mc.set_temp(tempTarget)
    time.sleep(2) # wait to exit stability conditions
    stable = "is stable"
    stable_id = mc.is_stable()
    while stable_id == 1:
        stable = "is not stable"
        temp = str(round(mc.get_temp(),2))
        print("query for loop stability, loop {}, ".format(stable) + "obj temp: " + temp)
        time.sleep(5)
        stable_id = mc.is_stable()
    if stable_id == 0:
        stable = "temperature regulation is not active"
    elif stable_id == 2:
        stable = "is stable"
    else:
        stable = "state is unknown"

    print("exit program with stability status: " + stable)
    mc.display_data()
    return stable

def readPeltierTemp(serial_hwid, tempTarget, configFile = "UNKNOWNconfFile.ini"):
    #port = connectSerialPort.connect_serial(serial_hwid)
    port = connectSerialPort.get_serial_port(serial_hwid)
    if serial_hwid  == serial_hwid_default:
        serial_hwid = connectSerialPort.get_serial_hwid_by_port(port)
        print("peltier_serial_hwid = " + serial_hwid)
        confFile.update(configFile, "TEMPBENCH", "peltier_serial_hwid", serial_hwid)
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")
    # initialize controller
    print(port)
    mc = Peltier(port)

    # get the values from DEFAULT_QUERIES
    mc.display_data()
    temp = str(round(mc.get_temp(),2))
    print("Peltier temp is: " + temp)
    return temp

if __name__ == '__main__':
    #serial_hwid = "UNKNOWN"
    serial_hwid = "0403:6015"
    nargs = len(sys.argv)
    if (nargs == 2):
        tempTarget = sys.argv[1]
    else:
        print("enter a temperature target in Celsius as argument")
        exit()
    ret = setPeltierTemp(serial_hwid, tempTarget)
    print(ret)
    ret = readPeltierTemp(serial_hwid, tempTarget)
    print(ret)
    #return ret
