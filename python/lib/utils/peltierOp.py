#!/usr/bin/env python
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: wrapper for Peltier control

import sys
sys.path.insert(0, '../../')  #ToDo: cleanup: move or remove this file
import basicSerialAuto


def setPeltierImmediate(termType, objInst):
    if termType == "mini":
        print ("To be implemented")
    else:
        print ("Set Peltier to: " + objInst.tempPeltier)
        basicSerialAuto.setPeltierImmediate(objInst)

def setPeltier(termType, objInst):
    if termType == "mini":
        print ("To be implemented")
    else:
        print ("Set Peltier to: " + objInst.tempPeltier)
        basicSerialAuto.setPeltier(objInst)

def readPeltier(termType, objInst):
    if termType == "mini":
        print ("To be implemented")
    else:
        print ("Read Peltier")
        return basicSerialAuto.readPeltier(objInst)
