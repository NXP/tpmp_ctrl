#!/usr/bin/env python3

# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Interactive command interface for TPMP (Thermo-regulated Power Management Platform)
# Pseudo Terminal interface to communicate with DUT (use regular shell commands)
# Additional set of command (type cmdlist for help) to interact with ACME and TEC-1091

import sys
import pexpect
from pexpect import fdpexpect
import time
import serial
import logging
import subprocess

from threading import Thread
from threading import Event

from lib.serial import connectSerialPort

from lib.utils import fileOp
from lib.utils import boardInit
from lib.utils import confFile

import re
from os.path import join, isfile
import shutil

#Py2*Py3 compatibility
import six
from six.moves import input
#from six.moves import configparser "this is not working, better use pip install configparser

import configparser
import signal
#import readline This is causing troubles due to readline called from thread

PELETIER_SERIAL_HWID_DEFAULT = "UNKNOWN"
BOARD_SERIAL_HWID_DEFAULT = "UNKNOWN"
BAUD_DEFAULT = 115200
BOARD_CONNECT_PATTERN_DEFAULT= "/unit_tests/autotest#"

#meerstetterPath_default = "./lib/meerstetter/pyMeCom/"
meerstetterPath_default = "./lib/meerstetter/"
cpdir_default = "../shell"
exitOnLauncherEnd_default = "False"
MATCHSHELL = "[a-zA-Z0-9_\-@]+[:][/a-zA-Z0-9_\-~]*[\s]*[#$]"

class SerialIf:
    def __init__(self, testTO, initLoop, consOutput, ser, configFile="default_config.ini", autoCompletion = True):
        Thread.__init__(self)
        self.testTO = testTO
        self.initLoop = initLoop
        self.consOutput = consOutput
        self.autoCompletion = autoCompletion
        self.testStatus = "Init"
        self.logFileStatus = "NOT_READY"
        stopper = Event()
        self.stopper = stopper
        self.serial = ser
        self.dieTemp = "Not Initialized"
        self.startTime = time.time()
        self.setDieTemp = "NOT STARTED"
        self.tempDieTarget = "25"
        self.configFile = configFile
        self.dirPath = "storedDirpath not initialized"
        self.completion = []
        self.threadType = "Test"
        self.checkRead = "uninitialized"
        config = configparser.ConfigParser()
        config.read(configFile)
        config.sections()

        self.copyMethod = config['TESTBOARD'].get('copyMethod', None)
        self.boardConnectPattern = config['TESTBOARD'].get('boardConnectPattern', BOARD_CONNECT_PATTERN_DEFAULT)
        self.cpdir = config['SHELL'].get('cpdir', cpdir_default)

        if self.copyMethod == "zmodem":
            self.copy_file = fileOp.rzmodem
        else:
            self.copy_file = fileOp.copy_file

        if "tempDieTarget" in config['TEMPBENCH']:
            self.tempbench = True

            self.tempPeltier = config['TEMPBENCH'].get('tempPeltier', None) #ToDo: set same default as config file
            self.tempDieTarget = config['TEMPBENCH'].get('tempDieTarget', None)
            self.deltaTargetHigh = config['TEMPBENCH'].get('deltaTargetHigh', None)
            self.deltaTargetLow = config['TEMPBENCH'].get('deltaTargetLow', None)
            self.limitLowHigh = config['TEMPBENCH'].get('limitLowHigh', None)
            self.warmUpAuto = config['TEMPBENCH'].get('warmUpAuto', None)
            self.maxPeltierTemp = config['TEMPBENCH'].get('maxPeltierTemp', None)
            self.maxBootTemp = config['TEMPBENCH'].get('maxBootTemp', None)
            self.peltier_serial_hwid = config['TEMPBENCH'].get('peltier_serial_hwid', PELETIER_SERIAL_HWID_DEFAULT)
            self.meerstetterPath = config['TEMPBENCH'].get('meerstetterPath', meerstetterPath_default)

            self.peltierPath = join(self.meerstetterPath, "tempcontrol.py")
            print("Peltier hwid initialized with : " + self.peltier_serial_hwid)
        else:
            self.tempbench = False

        self.acmecliPath = config['TESTS'].get('acmecliPath', "NOPATH")
        self.loginvite = config['TESTBOARD'].get('loginvite', "NOLOGINVITE")
        self.boardpwd = config['TESTBOARD'].get('boardpwd', "NOBOARDPWD")
        self.ttydev = join("/dev", config['TESTBOARD'].get('ttydev', 'ttymxc0'))
        self.acmeName = config['TESTS'].get('acmeName', "NONAME")
        self.onoffbox = config['TESTS'].get('onoffbox', "acme")

    def run(self):
        # code to execute during thread
        poleLoop(self, self.testTO, self.startTime, self.initLoop, self.consOutput, self.cpdir)

    def stop(self):
        print("stop: set stopper")
        self.stopper.set()

    def stopped(self):
        print("stopped: return stopper.is_set")
        return self.stopper.is_set()

        # needed for ubootconf

    def cmdwriter(self, cmd, sec):
        """\
        send write through serial for platform configuration.
        """
        self.serial.write(cmd.encode('ascii') + b'\r\n')
        time.sleep(sec)

class poleSerThread(Thread, SerialIf):
    def __init__(self, testTO, initLoop, consOutput, ser, configFile = "default_config.ini"):
        Thread.__init__(self)
        #autoCompletion is disabled when calling from thread to avoid readline issue
        SerialIf.__init__(self,testTO, initLoop, consOutput, ser, configFile, False)
        config = configparser.ConfigParser()
        config.read(configFile)
        config.sections()
        if 'exitOnLauncherEnd' in config['TESTS']:
            self.exitOnLauncherEnd = config['TESTS']['exitOnLauncherEnd']
        else:
            self.exitOnLauncherEnd = exitOnLauncherEnd_default

    def run(self):
        #code to execute during thread
        #poleLoop(self, self.testTO, self.startTime, self.initLoop, self.consOutput, self.cpdir)
        SerialIf.run(self)

    def stop(self):
        print("stop: set stopper")
        self.stopper.set()

    def stopped(self):
        print("stopped: return stopper.is_set")
        return self.stopper.is_set()

    def cmdwriter(self, cmd, sec):
        SerialIf.cmdwriter(self, cmd, sec)

def readDieTemp(fdp):
    disptxt = "READDIETEMP=$(cat /sys/devices/virtual/thermal/thermal_zone0/temp)"
    fdp.sendline(disptxt +'\r\n')
    disptxt = "echo Die Temperature: $READDIETEMP"
    fdp.sendline(disptxt +'\r\n')

def readDieTempCheck(fdp, objInst):
    print("readDieTempCheck")
    objInst.dieTemp = "Cleared for check"
    objInst.checkRead = "readDieTempCheck"
    readDieTemp(fdp)

def setPeltierImmediate(objInst):
    print("set Peltier: " + objInst.peltier_serial_hwid)
    if six.PY3:
        sys.path.insert(0, objInst.meerstetterPath)
        from lib.meerstetter import tempcontrol
        ret = tempcontrol.setPeltierTempImmediate(objInst.peltier_serial_hwid,objInst.tempPeltier, objInst.configFile)
    else:
		#ToDo tempcontrol changed, arguments to be added
        ret = subprocess.call("python3 " + objInst.peltierPath + " " + objInst.tempPeltier, shell=True)
    return ret

def setPeltier(objInst):
    print("set Peltier: " + objInst.peltier_serial_hwid)
    if six.PY3:
        sys.path.insert(0, objInst.meerstetterPath)
        from lib.meerstetter import tempcontrol
        ret = tempcontrol.setPeltierTemp(objInst.peltier_serial_hwid,objInst.tempPeltier, objInst.configFile)
    else:
        ret = subprocess.call("python3 " + objInst.peltierPath + " " + objInst.tempPeltier, shell=True)
    return ret

def readPeltier(objInst):
    print("read Peltier: " + objInst.peltier_serial_hwid)
    if six.PY3:
        sys.path.insert(0, objInst.meerstetterPath)
        from lib.meerstetter import tempcontrol
        ret = tempcontrol.readPeltierTemp(objInst.peltier_serial_hwid,objInst.tempPeltier, objInst.configFile)
    else:
		#ToDo to be modified to support read as argument
        ret = subprocess.call("python3 " + objInst.peltierPath + " " + objInst.tempPeltier, shell=True)
    return ret

def setDieTemp(objInst, serfd):
    deltaTargetHigh = int(objInst.deltaTargetHigh)
    deltaTargetLow = int(objInst.deltaTargetLow)
    limitLowHigh = int(objInst.limitLowHigh)
    fdp = serfd2fdp(serfd)

    if objInst.setDieTemp == "NOT STARTED" or objInst.setDieTemp == "STARTED BY LAUNCHER":
        if objInst.setDieTemp == "NOT STARTED":
            objInst.tempDieTarget = input('Enter Die temp Target:')
        if (int(float(objInst.tempDieTarget)) > limitLowHigh) :
            deltaTarget = deltaTargetHigh
            print("detect target High deltaTarget=" + str(deltaTarget) + "; objInst.tempDieTarget=" + objInst.tempDieTarget + "; limitLowHigh=" + str(limitLowHigh))
        else:
            deltaTarget = deltaTargetLow
            print("detect target Low deltaTarget=" + str(deltaTarget) + "; objInst.tempDieTarget=" + objInst.tempDieTarget + "; limitLowHigh=" + str(limitLowHigh))
        calcTempPeltier = int(objInst.tempDieTarget) - deltaTarget
        if calcTempPeltier <= int(objInst.maxPeltierTemp) :
            objInst.tempPeltier = str(calcTempPeltier)
        else:
            objInst.tempPeltier = objInst.maxPeltierTemp

        objInst.setDieTemp = "ITER1"
        print("execute initial readdietemp")
        readDieTempCheck(fdp, objInst)
        return False
    elif objInst.setDieTemp == "ITER1":
        if objInst.checkRead == "Check OK":
            print("read die OK readdietemp ITER1")
            tempDie = int(float(objInst.dieTemp))
            tempPeltier = int(float(readPeltier(objInst)))
            deltaPeltierDie = tempDie - tempPeltier
            tempDieTarget = int(float(objInst.tempDieTarget))
            deltaTargetDie = tempDieTarget - tempDie
            if 	0 <= deltaTargetDie <= 1:
                print("Die temp target is identical to current die temp")
                print("Peltier temp: " + objInst.tempPeltier + ", DieTemp: " + objInst.dieTemp + ", deltaPeltierDie: " + str(deltaPeltierDie))
                objInst.setDieTemp = "NOT STARTED"
                if objInst.warmUpAuto  == "True" :
                    print("STOP WARMUP Thread")
                    objInst.testStatus = "STOP WARMUP"
                    objInst.stop() #FixMe should not be needed but does not stop correcly if commented out
                return True
            else:
                setPeltier(objInst)
                objInst.setDieTemp = "STARTED"
                print("execute readdietemp ITER1 if setPeltier needed")
                readDieTempCheck(fdp, objInst)
                return False
        else:
            # error during read Die retry
            print("error detected retry readdietemp ITER1")
            readDieTempCheck(fdp,objInst)
            return False
    else:
        if objInst.checkRead == "Check OK":
            print("check OK readdie temp")
            tempDie = int(float(objInst.dieTemp))
            tempPeltier = int(float(objInst.tempPeltier))
            deltaPeltierDie = tempDie - tempPeltier
            tempDieTarget = int(float(objInst.tempDieTarget))
            deltaTargetDie = tempDieTarget - tempDie
            if 	0 <= deltaTargetDie <= 1:

                print("Die temp target reached")
                print("Peltier temp: " + objInst.tempPeltier + ", DieTemp: " + objInst.dieTemp + ", deltaPeltierDie: " + str(deltaPeltierDie))
                objInst.setDieTemp = "NOT STARTED"
                if objInst.warmUpAuto == "True" :
                    print("STOP WARMUP Thread")
                    objInst.testStatus = "STOP WARMUP"
                    objInst.stop() #FixMe should not be needed but does not stop correcly if commented out
                return True
            elif deltaTargetDie > 1:
                adjustDelta = round(deltaTargetDie/2,1)
                print("delta Peltier Die: " + str(deltaPeltierDie) + "delta Target Die: " + str(deltaTargetDie)+ "	adjusted delta: " + str(adjustDelta))
                calcTempPeltier = int(round(float(objInst.tempPeltier)) + adjustDelta)
                if calcTempPeltier <= int(objInst.maxPeltierTemp) :
                    objInst.tempPeltier = str(calcTempPeltier)
                else:
                    objInst.tempPeltier = objInst.maxPeltierTemp
                setPeltier(objInst)
                print("execute readdietemp deltaTargetDie > 1")
                readDieTempCheck(fdp,objInst)
                return False
            elif deltaTargetDie < 0:
                calcTempPeltier = int(round(float(objInst.tempPeltier)) - 1)
                if calcTempPeltier <= int(objInst.maxPeltierTemp) :
                    objInst.tempPeltier = str(calcTempPeltier)
                else:
                    objInst.tempPeltier = objInst.maxPeltierTemp
                setPeltier(objInst)
                print("execute readdietemp deltaTargetDie <<0")
                readDieTempCheck(fdp,objInst)
                return False
            else:
                print("ERROR SHOULD NOT BE HERE!!!!!!")
                readDieTempCheck(fdp, objInst)
                return False
        else:
            # error during read Die retry
            print("Error detected retry readdietemp ")
            readDieTempCheck(fdp,objInst)
            return False

def serfd2fdp(serfd):
    return pexpect.fdpexpect.fdspawn(serfd, timeout=0.2)

def exitTerm(objInst):
    print("exitTerm thread: " + objInst.name)
    exit()

def sendSerial(objInst, serfd, consOutput):
    deltaTargetHigh = 10
    deltaTargetLow = 4
    limitLowHigh = 60

    if objInst.autoCompletion:
        completion_init = ['cmdlist', 'exit', 'pole', 'shell', 'console', 'cpfile', 'cpexec', 'cpdir', 'peltier', 'readPeltier', 'peltierImmediate',
                           'dietemp','readDieTemp', 'rzmodem', 'szmodem', 'autocomplete', 'pwrcycle']
        import readline #conditional import is the only way to wa readline bug when called from thread

    def complete(text, state):
        for cmd in objInst.completion:
            if cmd.startswith(text):
                if not state:
                    return cmd
                else:
                    state -= 1

    def setCompletion(objInst):
        fdp.sendline('ls\r\n')
        try:
            purge = 0
            while not fdp.expect(MATCHSHELL):
                if purge == 0:
                    txtcompletion = fdp.before.decode('UTF-8')
                    txtcompletion = txtcompletion.replace(' ', ',')
                    txtcompletion = txtcompletion.replace('\r\n', ',')
                    txtcompletion = txtcompletion.replace('\n', ',')
                    txtcompletion = txtcompletion.replace('\t', ',')
                    txtcompletion = txtcompletion.replace(' ', ',')
                    txtcompletion = txtcompletion.replace(',,,', ',')
                    txtcompletion = txtcompletion.replace(',,', ',')
                    completion = txtcompletion.split(',')
                    objInst.completion = completion_init + completion
                    fdp.expect('[#/$]')  # wa to avoid repeated line
                    purge = 1
        except pexpect.TIMEOUT:
            logging.info('timeout {}')

    def otherCmd(cmd, objInst):
        changeDir = False
        fdp.sendline(cmd)
        try:
            purge = 0
            while not fdp.expect(MATCHSHELL):
                print(fdp.after.decode('UTF-8'))
                try:
                    # Below regex matches linux platforms
                    getBoardNames = re.match(r'(\w+)[@]([a-zA-Z0-9_\-]*)[:]([/a-zA-Z0-9_\-~]*)([#$])',
                                         fdp.after.decode('UTF-8'))
                    userName = getBoardNames.group(1)
                    boardName = getBoardNames.group(2)
                    dirPath = getBoardNames.group(3)
                    userRoot = getBoardNames.group(4)
                except:
                    # Below regex matches Android platforms
                    getBoardNames = re.match(r'([a-zA-Z0-9_\-]+)[:]([/a-zA-Z0-9_\-~]*)\s([#$])',
                                         fdp.after.decode('UTF-8'))
                    dirPath = getBoardNames.group(2)

                if dirPath != objInst.dirPath:
                    print('dirpath changed stored: ' + objInst.dirPath + '; new: ' + dirPath)
                    objInst.dirPath = dirPath
                    changeDir = True
                if purge == 0:
                    print(fdp.before.decode('UTF-8'))
                    fdp.expect('[#/$]')  # wa to avoid repeated line
                    purge = 1
        except pexpect.TIMEOUT:
            logging.info('timeout {}')
        if objInst.autoCompletion:
            if changeDir:
                setCompletion(objInst)

    fdp = serfd2fdp(serfd)
    if not fdp.isalive:
        objInst.stop()
        return objInst.testTO, consOutput
    while fdp.isalive():
        try:
            if objInst.setDieTemp == "NOT STARTED":
                if objInst.autoCompletion:
                    readline.parse_and_bind("tab: complete")
                    readline.set_completer(complete)
                cmd = input("Enter command (help: 'cmdlist') or 'exit':")
            else:
                cmd = 'dietemp'
            if cmd == 'exit':
                exitTerm(objInst)
            elif cmd == 'pole':
                cmd = input('Enter polling timeout:')
                print('Return to polling timeout set to:' + cmd)
                return int(cmd), consOutput
            elif cmd == 'console':
                if consOutput:
                    print('Current setting for console Output is ON')
                else:
                    print('Current setting for console Output is OFF')
                cmd = input('Console output ON/OFF:')
                if cmd == "ON":
                    consOutput = True
                    print('console Output is ON')
                else:
                    consOutput = False
                    print('console Output is OFF')
            elif cmd == 'cpfile':
                fileOp.copy_file_term(objInst)
            elif cmd == 'cpexec':
                fileOp.copy_execfile_term(objInst)
            elif cmd == 'cpdir':
                fileOp.copy_tree_term(objInst)
            elif cmd == 'peltier':
                objInst.tempPeltier = input('Enter peltier temp Target:')
                setPeltier(objInst)
            elif cmd == 'peltierImmediate':
                objInst.tempPeltier = input('Enter peltier temp Target:')
                setPeltierImmediate(objInst)
            elif cmd == 'readPeltier':
                readPeltier(objInst)
            elif cmd == 'dietemp':
                if not setDieTemp(objInst, fdp):
                    return 2, consOutput
                print('setdietemp completed return to pole')
                return 2, consOutput #return to Poleloop to stop thread cleanly
            elif cmd == 'readDieTempCheck':
                readDieTempCheck(fdp, objInst)
                return 1, consOutput
            elif cmd == 'readDieTemp':
                readDieTemp(fdp)
                return 1, consOutput
            elif cmd == 'rzmodem':
                fileOp.rzmodem_term(objInst)
            elif cmd == 'szmodem':
                fileOp.szmodem_term(objInst)
            elif cmd == 'autocomplete':
                if objInst.autoCompletion:
                    print('autocompletion is already ON')
                else:
                    print('autocompletion is OFF. default for threaded mode due to a bug')
                    cmd = input('confirm autocompletion activation (yes/no):')
                    if cmd == "yes":
                        objInst.autoCompletion = True
                        print('autocompletion enabled: ON \n'
                              'WARNING: if called from testLauncher and exit script with CTRL+C\n'
                              'a bug in readline will disable terminal echo\n'
                              'recovery from terminal type: stty sane')
                    else:
                        print('cancel autocompletion activation')
            elif cmd == 'pwrcycle':
                if objInst.acmeName == "NONAME":
                    print("No name defined for ACME in conf file pwrcycle cannot be issued")
                elif objInst.acmecliPath == "NOPATH":
                    print("path for acmeCli: acmecliPath not initialized in conf file pwrcycle cannot be issued")
                else:
                    if not boardInit.powerCycleBoard(objInst.acmecliPath, objInst.acmeName, objInst.onoffbox):
                        boardInit.reboot(objInst)
                    return 10, consOutput
                #else:  cannot be disabled on the fly, once import
                #    objInst.autoCompletion = False
                #    print('autocompletion disabled: OFF')
            elif cmd == 'cmdlist':
                print('commands')
                print('-- cmdlist: Displays this help')
                print('-- help: regular shell help')
                print('-- exit to quit\n-- pole to get pack to polling mode\n-- shell commands to keep stay in interactive mode')
                print('-- console to configure serial Output ON/OFF for debug')
                print('-- cpfile to copy txt file from host to target current dir')
                print('-- cpexec to copy binary file from host to target current dir')
                print('-- cpdir to copy entire dir from host to current dir')
                print('-- peltier to set temp for Peltier setup and wait for stabilization')
                print('-- peltierImmediate to set temp for Peltier setup wo wait time')
                print('-- readPeltier to read current Peltier Object temperature')
                print('-- dietemp to set temp for die adjusted automatically through peltier')
                print('-- readDieTemp to read die temp')
                print('-- rzmodem to copy file from host to target')
                print('-- szmodem to copy file from target to host')
                print('-- autocomplete to enable autocompletion when not activated by default')
                print('-- pwrcycle to shut down pwr through acme then pwron and bootup')

            else:
                otherCmd(cmd, objInst)
                print('objInst.dirPath: ' + objInst.dirPath)

        except KeyboardInterrupt:
            objInst.testStatus = "KEYBOARD INTERRUPT"
            return 1, consOutput

def boardConnected(fdp, boardConnectPattern):
    try:
        fdp.expect(boardConnectPattern)
        print("Board Connection pattern identified")
        return True
    except pexpect.TIMEOUT:
        print("TIMEOUT Board Connection failed retrying")
        return False

def poleLoop(objInst, testTO, startTime, initLoop = False, consOutput = True, cpdir = cpdir_default):
    # open the serial port
    txtTable = ["teardown", "stop autoboot", objInst.loginvite, "--TEST END--", "--TEST-LAUNCHER END--", "--TEST start: ","--POWER PROBE Start:", "--POWER PROBE End:", "\n", "Die Temperature: [0-9]{5}[0-9]*"]

    ser = objInst.serial
    ser.flushInput()
    changeFdp = False
    fdp = pexpect.fdpexpect.fdspawn(ser.fd, timeout=testTO)
    boardreboot = False
    tempFile = open("templog.txt","w")
    tempFile.write("timestamp(s)	die temperature\n")
    serLog = open("seriallog.txt","w")
    readCheckTO = False
    MAXREADCNT = 7
    readCheckCnt = MAXREADCNT

    def boardInitComplete(objInst, ser):
    # ToDo this is not working use return value from autotestconf instead?
        objInst.testStatus = "BOARD INIT COMPLETED"
        print("BOARD INIT COMPLETED ")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(5)  # Needed to sync-up and catch event
        if objInst.threadType == "Init":
            print("stop init thread")
            objInst.stop()

    while not objInst.stopper.is_set():
        if changeFdp:
            if ser.isOpen():
                testTO, consOutput = sendSerial(objInst, ser.fd, consOutput)
                print('return sendserial change fdp test status: ' + objInst.testStatus)
                if objInst.testStatus == "STOP WARMUP":
                    print("STOP WARMUP")
                    objInst.stop()
                if objInst.testStatus == "KEYBOARD INTERRUPT":
                    print("KEYBOARD INTERRUPT")
                    objInst.stop()
                fdp = pexpect.fdpexpect.fdspawn(ser.fd, timeout=testTO)
            else:
                exit()
            changeFdp = False
        if objInst.checkRead == "readDieTempCheck":
            if readCheckTO == True:
                print("ERROR invalid Die Temp Read")
                readCheckCnt = MAXREADCNT
                readCheckTO = False
            elif objInst.dieTemp == "Cleared for check":
                time.sleep(0.1)
                readCheckCnt = readCheckCnt - 1
                if readCheckCnt == 0:
                    readCheckTO = True
                    objInst.checkRead == "read Die Temp Error Status"
            else:
                readCheckTO = False
                print("valid Die Temp Read cnt= " + str(readCheckCnt))
                readCheckCnt = MAXREADCNT
                objInst.checkRead = "Check OK"
        try:
            fdp.expect(txtTable) # wait for key word
        except pexpect.TIMEOUT:
            logging.info('timeout {}')
            if initLoop:
                print("Initialise")
                initLoop = False
            else:
                print("CONSOLE TIMEOUT")
                objInst.testStatus = "CONS_TIMEOUT"
            changeFdp = True
        except pexpect.EOF:
            #logging.info('Cannot reach the console {}'.format(ser))
            print("EOF")
        if fdp.after:
            try:
                serLog.write(str(fdp.before.decode('UTF-8')))
            except:
                print("Error writing serial output to file")
            if "teardown" in str(fdp.after):
                print("find " + "teardown")
                objInst.testStatus = "find " + "teardown"
            elif "stop autoboot" in  str(fdp.after):
                print("UBOOT print identified")
                objInst.testStatus = "UBOOT"
                boardreboot = True
                boardInit.ubootconf(objInst)
                if objInst.loginvite == "nologinrequired":
                    print("waiting for boot completion")
                    time.sleep(20)
                    boardreboot = False
                    boardInit.autoconfnolog(objInst, cpdir)
                    boardInitComplete(objInst, ser)
                    #enter su if boardpwd is root
                    #ToDo change name confusing
                    if objInst.boardpwd == "root":
                        fdp.sendline("su\n")
            elif objInst.loginvite in str(fdp.after) and (boardreboot):
                print("catch enter password to login ")
                objInst.testStatus = "LOGIN "
                boardreboot = False
                boardInit.autotestconf(objInst, cpdir)
                maxTrial = 10
                while not (boardConnected(fdp, objInst.boardConnectPattern) or maxTrial <= 0):
	                maxTrial -= 1
	                boardInit.autotestconf(objInst, cpdir)
                if maxTrial <= 0:
                    print("ERROR: fail to connect board \n"
                          "   connexion tentative with boardpwd: " + objInst.boardpwd + "\n"
                          "   cannot reach target: " + objInst.boardConnectPattern)
                    exit()
                boardInitComplete(objInst, ser)
            elif "--TEST start: " in str(fdp.after):
                print("TEST START ")
                serLog.write("Detect TEST START \n")
                objInst.testStatus = "Test_Started"
                print("objInst.testStatus: " + objInst.testStatus)
            elif "--POWER PROBE Start:" in str(fdp.after):
                print("Detect PROBE START ")
                serLog.write("PROBE START \n")
                objInst.testStatus = "PROBE STARTED"
                print("objInst.testStatus: " + objInst.testStatus)
            elif "--POWER PROBE End: " in str(fdp.after):
                print("Detect PROBE END ")
                serLog.write("POWER PROBE END \n")
                objInst.testStatus = "PROBE FINISHED"
                print("objInst.testStatus: " + objInst.testStatus)
            elif "Die Temperature: " in str(fdp.after):
                matchObj = re.match( r'Die Temperature: ([0-9]*)', fdp.after.decode('UTF-8'))
                if matchObj:
                    print("Read Die Temperature")
                    objInst.dieTemp = str(int(matchObj.group(1))/1000)
                    timestamp = time.time() - objInst.startTime
                    print("objInst.dieTemp: " + objInst.dieTemp + " " + "timestamp: " + str(int(timestamp)))
                    serLog.write(str(int(timestamp)) + "	" + objInst.dieTemp + "\n")
                    tempFile.write(str(int(timestamp)) + "	" + objInst.dieTemp + "\n")
                else:
                    print("No Match: " + str(fdp.after))

            elif "--TEST END--" in str(fdp.after):
                if objInst.testStatus == "find " + "teardown":
                    print("Detect valid TEST END")
                    serLog.write("valid TEST END \n")
                    objInst.testStatus = "TEST_END"
                else:
                    print("Detect invalid TEST END")
                    serLog.write("invalid TEST END \n")
                #save serial log in prev buffer then reopen immediately for next test
                serLog.close()
                print(">>>creation of seriallogPrev.txt")
                shutil.move("seriallog.txt", "seriallogPrev.txt")
                objInst.logFileStatus = "LOGFILE_READY"
                serLog = open("seriallog.txt","w")
            elif "--TEST-LAUNCHER END--" in str(fdp.after):
                print("Detect TEST LAUNCHER END")
                serLog.write("TEST LAUNCHER END \n")
                #testTO, consOutput = sendSerial(objInst, ser.fd, consOutput)
                if objInst.exitOnLauncherEnd == "True":
                    objInst.stop()
                else:
                    sendSerial(objInst, ser.fd, consOutput)
                    print('return sendserial END')
            elif consOutput and ("\n" in str(fdp.after)):
                print(str(fdp.before))
            #else:
                #print("FAIL find any text")
    tempFile.close()
    serLog.close()

def main(configFile = "default_config.ini", testTO = 1, initLoop = True, consOutput = False):
    nargs = len(sys.argv)
    if (nargs >= 2):
        configFile = sys.argv[1]
    if not isfile(configFile):
        print("Config file does not exist creation:")
        confFile.create(configFile)
    config = configparser.ConfigParser()
    config.read(configFile)
    config.sections()

    board_serial_hwid= config['TESTBOARD'].get('board_serial_hwid', BOARD_SERIAL_HWID_DEFAULT)
    baud= config['TESTBOARD'].get('baud', BAUD_DEFAULT)
    board_serial_port = config['TESTBOARD'].get('board_serial_port', "0")

    # open the serial port
    ser = connectSerialPort.connect_serial(board_serial_hwid, baud, board_serial_port)
    if board_serial_hwid  == BOARD_SERIAL_HWID_DEFAULT:
        board_serial_hwid = connectSerialPort.get_serial_hwid_by_port(ser.port)
        print("board_serial_hwid = " + board_serial_hwid)
        confFile.update(configFile, "TESTBOARD","board_serial_hwid" ,board_serial_hwid)
    ser.flushInput()
    if ser.isOpen():
         print(ser.name + ' is open...')

    interface = SerialIf(testTO, initLoop, consOutput, ser, configFile)
    interface.name = 'basicSerial'
    interface.run()
if __name__ == '__main__':
    main()
