#!/usr/bin/env python
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Utils for conf file management

import configparser

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

def create(configFilePath):
    config = configparser.ConfigParser()
    config['TEMPBENCH'] = {}
    config['TESTBOARD'] = {}
    config['TESTS'] = {}
    config['SHELL'] = {}
    with open(configFilePath, 'w') as configfile:
        config.write(configfile)

def update(configFilePath, section, varName, varVal):
    config = configparser.ConfigParser()
    config.read(configFilePath)
    config.sections()
    if not section in config:
        config.add_section(section)
    config.set(section, varName, varVal)
    with open(configFilePath, 'r+') as configfile:
        config.write(configfile)
    print("write: " + varName + "=" + varVal + " to section " + section + "in file: " + configFilePath)
