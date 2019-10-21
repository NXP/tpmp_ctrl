#!/usr/bin/env python
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Utils for board reboot. Describe sequences for reboot/power cycle

import sys
import serial

from lib.utils import fileOp
sys.path.insert(0, '../../')
import escapesh
import six
from lib.utils import peltierOp
import subprocess
import time
OK = True
ERR = False

def autotestconf(objInst, srcpath=None, tmppath = "../tmp_shell"):
    print("enter pwd: " + objInst.boardpwd)
    objInst.cmdwriter("\n",2)
    objInst.cmdwriter(objInst.boardpwd + "\n",2)
    autoconfnolog(objInst, srcpath, tmppath)

def autoconfnolog(objInst, srcpath=None, tmppath = "../tmp_shell"):
    testdir = objInst.boardConnectPattern[:-1]
    objInst.cmdwriter("mkdir " + testdir  + "\n",1)
    objInst.cmdwriter("cd " + testdir + "\n",2)
    if srcpath is not None:
        if six.PY2:
            escapesh.escape(srcpath, tmppath) #needed only when txtcopy is used

        if objInst.threadType == "Init":  # set only at first reboot when prepareboard = True
            fileOp.copy_dir(objInst, srcpath + "/", dstpath = ".") #overriden to tmppath for txtcopy
    objInst.cmdwriter("chmod 777 " + testdir + " -R\n",2)
    objInst.serial.flush()

def ubootconf(objInst):
    objInst.cmdwriter("\n",1)
    send_cmd_from_file(objInst, "ubootcfg.txt", "../uboot/")
    objInst.cmdwriter("boot\n",1)

def send_cmd_from_file(objInst, filename, srcpath):
    """Ask user for filename and copy in local file"""
    srcfile = srcpath + filename
    try:
        with open(srcfile, 'rb') as f:
            sys.stderr.write('--- Sending file {} ---\n'.format(srcfile)) #FSY: ???
            for line in f:
                block = line.rstrip("\r\n")
                if not block:
                    break
                objInst.cmdwriter(block + "\n", 1)                             # Wait for output buffer to drain.
            sys.stderr.write('\n--- Commands from File {} sent ---\n'.format(srcfile))
    except IOError as e:
        sys.stderr.write('--- ERROR opening file {}: {} ---\n'.format(filename, e))

def powerCycleBoard(acmecliPath, acmeName):
    print("Reboot the board: Switch OFF")
    cmd =  acmecliPath + "acme-cli -s " + acmeName + " switch_off 1"
    print(cmd)
    ret = subprocess.call(cmd, shell=True)
    #ToDo incorrect returning fail in any case
    if ret != 0:
        print("FAIL to power DOWN the board through ACME")
        print("ERROR Code: " + str(ret))
    time.sleep(1)
    cmd =  acmecliPath + "acme-cli -s " + acmeName + " switch_on 1"
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        print("FAIL to power ON the board through ACME")
        print("ERROR Code: " + str(ret))
    print("Switch board power ON")

def reboot(threadID):
    threadID.cmdwriter("reboot\n", 1)

def powerCycleBoard(acmecliPath, acmeName, onoffbox= "acme"):
    print("Reboot the board: Switch OFF")
    ret = True
    if onoffbox == "acme":
        cmd =  acmecliPath + "acme-cli -s " + acmeName + " switch_off 1"
        print(cmd)
        ret = subprocess.call(cmd, shell=True)
        #ToDo incorrect returning fail in any case
        if ret != 0:
            print("FAIL to power DOWN the board through ACME")
            print("ERROR Code: " + str(ret))
        time.sleep(1)
        cmd =  acmecliPath + "acme-cli -s " + acmeName + " switch_on 1"
        ret = subprocess.call(cmd, shell=True)
        if ret != 0:
            print("FAIL to power ON the board through ACME")
            print("ERROR Code: " + str(ret))
        print("Switch board power ON")
    elif onoffbox == "energenie":
        cmd = "egctl PMS2-LAN off off off off"
        print(cmd)
        ret = subprocess.call(cmd, shell=True)
        if ret != 0:
            print("FAIL to power DOWN the board through energenie")
            print("ERROR Code: " + str(ret))
        time.sleep(1)
        cmd = "egctl PMS2-LAN on off off off"
        ret = subprocess.call(cmd, shell=True)
        if ret != 0:
            print("FAIL to power ON the board through energenie")
            print("ERROR Code: " + str(ret))
        print("Switch board power ON")
    else:
        print("!!!!!!!!!!!!!!!!!!!!!ON OFF BOX not supported simple reboot instead!!!!!!!!!!!!!!!!!!!!!!!!")
        ret = False
    return ret

def rebootBoardSeq(acmecliPath, acmeName, threadID, termType = "basic", onoffbox= "acme"):
    if threadID.tempbench:
        savedPeltierTemp = peltierOp.readPeltier(termType, threadID)
        restorePeltier = False
        if savedPeltierTemp >= threadID.maxBootTemp :
            threadID.tempPeltier = threadID.maxBootTemp
            peltierOp.setPeltier(termType, threadID)
            restorePeltier = True

    retryuboot = 10
    retryboardinit = 10
    if threadID.testStatus == "Not implemented" :
        print("boot boardseq 1-onoffbox = " + onoffbox)
        if not powerCycleBoard(acmecliPath, acmeName, onoffbox):
            print("FAIL: powerCycleBoard did not succeed, issue simple reboot instead")
            reboot(threadID)
        time.sleep(40)
    else:
        while  threadID.testStatus != "UBOOT" and retryuboot >= 0:
            print("testStatus= " +  threadID.testStatus)
            print("boot boardseq 2-onoffbox = " + onoffbox)
            if not powerCycleBoard(acmecliPath, acmeName, onoffbox):
                reboot(threadID)
            retryuboot = retryuboot - 1
            time.sleep(5)
        if retryuboot == 0:
            return ERR
        while  threadID.testStatus != "BOARD INIT COMPLETED" and retryboardinit >= 0:
            retryboardinit = retryboardinit - 1
            time.sleep(5)
            print("Waiting for board init completion")
            print("expecting loginvite: " + threadID.loginvite)
            threadID.cmdwriter("\n", 1) #force print invite again
        if retryboardinit == 0:
            return ERR
    time.sleep(10) # Why is this latency needed??? Detect TEST START missed wo

    if threadID.tempbench:
        if restorePeltier:
            threadID.tempPeltier = savedPeltierTemp
            peltierOp.setPeltier(termType, threadID)
    return OK

def rebootBoard(acmecliPath, acmeName, threadID, termType = "basic", onoffbox= "acme"):
    retryboot = 4
    while retryboot > 0:
        retryboot = retryboot - 1
        print("reboot board onoffbox = " + onoffbox)
        if rebootBoardSeq(acmecliPath, acmeName, threadID, termType, onoffbox):
            return OK
    return ERR
