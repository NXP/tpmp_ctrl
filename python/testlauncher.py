#!/usr/bin/env python
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Test Launcher used to launch a test suite on DUT
# Serial interface is used to sync-up
# Can be used with tpmp or in stand alone mode

import codecs
import os
import sys
import threading
import subprocess
#from subprocess import Popen, PIPE, STDOUT
import string

from threading import Thread

import serial
from serial.tools.list_ports import comports
from serial.tools import hexlify_codec

from os import listdir
from os.path import isfile, isdir, join

import time
import minitermcust
import basicSerialAuto

from lib.serial import connectSerialPort

from lib.utils import fileOp
from lib.utils import confFile
from lib.utils.confFile import str2bool
import ast
from lib.utils import sendMailConf
from lib.utils import boardInit
from lib.utils import peltierOp


#Py2*Py3 compatibility
import six
from six.moves import input
#from six.moves import configparser "this is not working, better use pip install configparser

import configparser
import shutil
from distutils.dir_util import copy_tree

peltier_serial_hwid_default = "UNKNOWN"
board_serial_hwid_default = "UNKNOWN"
baud_default = 115200
termType_default = "basic"
onoffbox_default = "acme"

logFilesPath = "./logFiles/"
testPath = "./"

OK = True
ERR = False

class startMiniterm(Thread):

    def __init__(self, custAttribute):
        Thread.__init__(self)
        self.custAttribute = None
        self.testStatus = "Not implemented"

    def run(self):
        #code to execute during thread
        #minitermcust.main("/dev/ttyUSB0", 115200)
        #os.system("python ./minitermcust.py /dev/ttyUSB3 115200 --filter colorize")
        subprocess.call("python ./minitermcust.py /dev/ttyUSB0 115200 --filter colorize --cpdir ../raw_shell/", shell=True)

    def readConsole(self, text):
        minitermcust.ConsoleBase.write(self._start_reader, text)

class runTestThread(threading.Thread):

    def __init__(self, ser, testPath, testName, duration):
        Thread.__init__(self)
        self.testPath = testPath
        self.testName = testName
        self.duration = duration
        self.ser = ser
        self._stop_event = threading.Event()

    def run(self):
        #code to execute during thread
        runTest(self.ser, self.testPath, self.testName, self.duration)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

'''def powerCycleBoard(acmecliPath, acmeName):
    print("Reboot the board: Switch OFF")
    cmd =  acmecliPath + "acme-cli -s " + acmeName + " switch_off 1"
    print(cmd)
    ret = subprocess.call(cmd, shell=True)
    #ToDo incorrect returning fail in any case
    if ret != "Success":
        print("FAIL to power DOWN the board through ACME")
    time.sleep(1)
    cmd =  acmecliPath + "acme-cli -s " + acmeName + " switch_on 1"
    ret = subprocess.call(cmd, shell=True)
    if ret != "Success":
        print("FAIL to power ON the board through ACME")
    print("Switch board power ON")

def rebootBoard(acmecliPath, acmeName, threadID, termType = "basic"):
    savedPeltierTemp = peltierOp.readPeltier(termType, threadID)
    restorePeltier = False
    if savedPeltierTemp >= threadID.maxBootTemp :
        threadID.tempPeltier = threadID.maxBootTemp
        peltierOp.setPeltier(termType, threadID)
        restorePeltier = True
    if threadID.testStatus == "Not implemented" :
        boardInit.powerCycleBoard(acmecliPath, acmeName)
        time.sleep(40)
    else:
        while  threadID.testStatus != "UBOOT":
            print("testStatus= " +  threadID.testStatus)
            boardInit.powerCycleBoard(acmecliPath, acmeName)
            time.sleep(5)
        while  threadID.testStatus != "BOARD INIT COMPLETED":
            time.sleep(5)
            print("Waiting for board init completion")
    time.sleep(10) # Why is this latency needed??? Detect TEST START missed wo
    if restorePeltier:
        threadID.tempPeltier = savedPeltierTemp
        peltierOp.setPeltier(termType, threadID)'''

def rebootBoardOnInit(acmecliPath, acmeName, threadID, termType, bootBoardInit, onoffbox):
    if bootBoardInit == "True":
        if boardInit.rebootBoard(acmecliPath, acmeName, threadID, termType, onoffbox):
            bootBoardInit == "Done"
        else:
            print("ERROR: Fail to reboot the board multiple times, exit test launcher.")
            exit()
    return bootBoardInit

def sendserial(cmd, ser):

    if ser.isOpen():
        print(ser.name + ' is open for send...')

        ser.write(cmd.encode() + b"\r\n")
        time.sleep(1)

        if cmd == 'exit':
            ser.close()
            print(ser.name + ' is closed...')
        #exit()
    else:
        print("Error " + ser.name + ' is not open...')

def rcvserial(cmd):

    noMatch = True
    while noMatch:
        line = sys.stdin.readline().rstrip('\r\n')
        if cmd in line:
            print("===============================TEST END Detected============================")
            return cmd

#This logging style is too intrusive, affect CPU load when buffer is copied
def runTest(ser, testPath, testName, duration = "1000", TFTDuration = "50", bg = False):
    print(">> runTest: Name = " + testName + " duration = " + duration)
    if bg:
        cmd =  testPath + testName + " " + duration + " " + TFTDuration +  " | tee " + logFilesPath + testName + ".log.txt &"
    else:
        cmd =  testPath + testName + " " + duration + " " + TFTDuration + " | tee " + logFilesPath + testName + ".log.txt"
    sendserial(cmd, ser)

def runTestNoLog(ser, testPath, testName, duration = "1000", TFTDuration = "50",bg = False):
    print(">> runTest: Name = " + testName + " duration = " + duration)
    if bg:
        cmd =  testPath + testName + " " + duration + " " + TFTDuration + "  &"
    else:
        cmd =  testPath + testName + " " + duration + " " + TFTDuration
    sendserial(cmd, ser)

def stopTest(ser):
    cmd = "\x03"
    sendserial(cmd, ser)

    time.sleep(1)
    cmd = "./teardown.sh"
    sendserial(cmd, ser)
    cmd = "./teardownCM.sh"
    sendserial(cmd, ser)
    cmd = "./teardownGLS.sh"
    sendserial(cmd, ser)

def createTestLog(testName, ser, results):
    cmd =  "dmesg > " + logFilesPath + testName + ".dmesg.log.txt"
    sendserial(cmd, ser)
    time.sleep(5)
    cmd =  "dmesg --clear"
    sendserial(cmd, ser)
    resultsPath = join("..", results)
    serLogName = (testName + ".log.txt")
    serLogPath = join(resultsPath, serLogName)
    shutil.copyfile("seriallogPrev.txt", serLogPath)

def saveLog2Host(testName, ser, logFilesPath, results, objInst):
    cmd =  "cd " + logFilesPath
    sendserial(cmd, ser)
    time.sleep(1)
    resultsPath= join("..", results)
    if not isdir(resultsPath):
        os.mkdir(resultsPath)
    fileOp.szmodem(objInst, testName + ".dmesg.log.txt", resultsPath, objInst.ttydev.encode())
    time.sleep(1)
    #fileOp.szmodem(objInst, testName + ".log.txt", resultsPath, objInst.ttydev.encode())
    #time.sleep(1)
    cmd =  "cd .."
    sendserial(cmd, ser)
    time.sleep(1)

def frameworkTeardown(termType, testTimeout):
    if termType == "basic":
        thread_term = basicSerialAuto.poleSerThread(testTimeout, True, False)
        thread_term.start()

def startTermThread(termType, testTimeout, ser, configFile):
    if termType == "mini":
        #minitermcust.main("/dev/ttyUSB2", 115200)
        thread_term = startMiniterm("MiniTerm1")
        thread_term.start()
        #os.system("python ./minitermcust.py /dev/ttyUSB3 115200 --filter colorize")
    else:
        thread_term = basicSerialAuto.poleSerThread(testTimeout, False, False, ser, configFile)
        thread_term.start()
    time.sleep(5)
    return thread_term

def startTermInst(termType, testTimeout, ser, configFile, initLoop = False):
    if termType == "mini":
        #minitermcust.main("/dev/ttyUSB2", 115200)
        inst_term = startMiniterm("MiniTerm1")
        inst_term.start()
        #os.system("python ./minitermcust.py /dev/ttyUSB3 115200 --filter colorize")
    else:
        inst_term = basicSerialAuto.SerialIf(testTimeout, initLoop, False, ser, configFile)
        #inst_term.start()
    time.sleep(5)
    return inst_term

'''def setPeltierImmediate(termType, objInst):
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
        return basicSerialAuto.readPeltier(objInst) '''

def warmUp(termType, objInst):
    timeout = 2000
    if termType == "mini":
        print ("To be implemented")
    else:
        print ("#### Warm Up Die to value set in config file ####")
        print ("Set Die to: " + objInst.tempDieTarget)
        objInst.setDieTemp = "STARTED BY LAUNCHER"
        objInst.testStatus = "START WARMUP"
        basicSerialAuto.setDieTemp(objInst, objInst.serial.fd)
        print("objInst.setDieTemp: " + objInst.setDieTemp)
        print('timeout: ' + str(timeout))
        while objInst.setDieTemp != "NOT STARTED" and timeout >= 0 :
            time.sleep(5)
            print("Warm.up on going")
            timeout = timeout - 5
            print("objInst.setDieTemp: " + objInst.setDieTemp)
            print('timeout: ' + str(timeout))

def waitTestEnd(thread_term, testName, testTimeout, ser):
    FwkTO = testTimeout
    while not (thread_term.testStatus == "TEST_END" or FwkTO <= 0):
        FwkTO -= 1
        time.sleep(1)
    if thread_term.testStatus != "TEST_END":
       print("\n Test timeout Detected by Framework, Force stop:" + testName)
       stopTest(ser)
       return ERR
    else:
        print("Test " + testName + " Status: " + thread_term.testStatus)
        return OK

def waitLogFile(thread_term, testName):
    timeout = 10
    while not ( thread_term.logFileStatus == "LOGFILE_READY" or timeout <= 0):
        timeout -= 1
        time.sleep(1)
        print("logfile status = " + thread_term.logFileStatus)
    if thread_term.logFileStatus != "LOGFILE_READY":
       print("\n log file generation failure for test:" + testName)
       return ERR
    else:
        print("log file generation for " + testName + " Succeeded: ")
        return OK

def probePower(testName, probeList, pyacmecaptureParams, probeDuration, resultsDir, acmeName):
    #print(os.environ["PATH"])
    pyacmecapturePath, pyacmecaptureVersion, pyacmecaptureSlots = pyacmecaptureParams
    saveDir = os.getcwd()
    resultsPath= join(saveDir, "..", resultsDir)
    if not isdir(resultsPath):
        os.mkdir(resultsPath)
    #resultsPath= join(resultsPath, testName)
    #print("echo ACME POWER MEASUREMENTS > " + testName + "_pwr.txt")
    print("echo ACME POWER MEASUREMENTS > " + resultsPath + testName + "_pwr.txt")
    os.chdir(pyacmecapturePath)
    print(os.getcwd())
    if pyacmecaptureVersion == "0.4":
        print("pyacmecature version: " + pyacmecaptureVersion)
        sep = " "
        probeNames = sep.join(probeList)
        print("python ./pyacmecapture.py --p " + acmeName + ":" + pyacmecaptureSlots + " -d " + probeDuration + " -n " + probeNames + " -od " + resultsPath + " -o " + testName)
        subprocess.call("python ./pyacmecapture.py --p " + acmeName + ":" + pyacmecaptureSlots + " -d " + probeDuration + " -n " + probeNames + " -od " + resultsPath + " -o " + testName, shell=True)
    else:
        print("pyacmecature version undefined: " + pyacmecaptureVersion)
        probeCnt = len(probeList)
        sep = ","
        probeNames = sep.join(probeList)
        print("python ./pyacmecapture.py --ip " + acmeName + " -d " + probeDuration + " -c " + str(probeCnt) + " -n " + probeNames + " -od " + resultsPath + " -o " + testName)
        subprocess.call("python ./pyacmecapture.py --ip " + acmeName + " -d " + probeDuration + " -c " + str(probeCnt) + " -n " + probeNames + " -od " + resultsPath + " -o " + testName, shell=True)
    os.chdir(saveDir)

#def str2bool(v):
#  return v.lower() in ("yes", "true", "t", "1")

def main(configFile = "default_config.ini"):
    #ports = get_serial_port_by_hwid(serial_hwid)
    #if (len(ports) >> 0):
    #    port = ports[0]
    #    print("identify port by hwid:" + port)
    #else:
    #    ask_for_port()
    #ser = serial.Serial(port, baud, timeout=1)
    nargs = len(sys.argv)
    if (nargs >= 2):
        configFile = sys.argv[1]
    if not isfile(configFile):
        print("Config file does not exist creation:")
        confFile.create(configFile)
    config = configparser.ConfigParser()
    config.read(configFile)
    config.sections()
    if 'board_serial_hwid' in config['TESTBOARD'] :
        #print('detect board serial hwid')
        board_serial_hwid = config['TESTBOARD']['board_serial_hwid']
    else:
        board_serial_hwid = board_serial_hwid_default
    if 'baud' in config['TESTBOARD'] :
        baud = config['TESTBOARD']['baud']
    else:
        baud = baud_default
    if 'board_serial_port' in config['TESTBOARD'] :
        board_serial_port = config['TESTBOARD']['board_serial_port']
    else:
        board_serial_port = "0"
    ser = connectSerialPort.connect_serial(board_serial_hwid, baud, board_serial_port)
    if board_serial_hwid  == board_serial_hwid_default:
        board_serial_hwid = connectSerialPort.get_serial_hwid_by_port(ser.port)
        print("board_serial_hwid = " + board_serial_hwid)
        confFile.update(configFile, "TESTBOARD","board_serial_hwid" ,board_serial_hwid)
    ####INIT from conf file###########
    if 'testTO' in config['TESTS'] :
        testTimeout = int(config['TESTS']['testTO'])
        #print(">>>>>>>>>>>>testTO read from conf file: " + str(testTimeout))
    else:
        print("testTO init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","testTO" ,"INIT Value needed")
        exit()
    if 'termType' in config['TESTS'] :
        termType = config['TESTS']['termType']
        #print(">>>>>>>>>>>>term type read from conf file: " + termType)
    else:
        print("termType init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS", "termType", termType_default)
    if 'bootBoardInit' in config['TESTS'] :
        bootBoardInit = config['TESTS']['bootBoardInit']
    else:
        print("bootBoardInit init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","bootBoardInit" ,"INIT Value needed")
        exit()
    if 'rebootAfterEachTest' in config['TESTS'] :
        rebootAfterEachTest = config['TESTS']['rebootAfterEachTest']
    if 'rebootOnFailure' in config['TESTS'] :
        rebootOnFailure = config['TESTS']['rebootOnFailure']
    if 'testDuration' in config['TESTS'] :
        testDuration = config['TESTS']['testDuration']
    else:
        print("testDuration init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","testDuration" ,"INIT Value needed")
        exit()
    if 'probeDuration' in config['TESTS'] :
        probeDuration = int(config['TESTS']['probeDuration'])
    else:
        print("probeDuration init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","probeDuration" ,"INIT Value needed")
        exit()
    if 'testList' in config['TESTS'] :
        testList = ast.literal_eval(config.get('TESTS', 'testList'))
        #testList = config['TESTS']['testList']
        #print(type(testList))
        #print (testList)
    else:
        print("testList init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","testList" ,"INIT Value needed")
        exit()
    if 'acmegraph' in config['TESTS'] :
        acmegraph = str2bool(config['TESTS']['acmegraph'])
    else:
        print("acmegraph init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","acmegraph" ,"INIT Value needed")
        exit()
    if 'prepareBoard' in config['TESTS'] :
        prepareBoard = str2bool(config['TESTS']['prepareBoard'])
    if 'acmecliPath' in config['TESTS'] :
        acmecliPath = config['TESTS']['acmecliPath']
    else:
        print("acmecliPath init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","acmecliPath" ,"INIT Value needed")
        exit()
    if 'acmeName' in config['TESTS'] :
        acmeName = config['TESTS']['acmeName']
    else:
        print("acmeName init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","acmeName" ,"INIT Value needed")
        exit()
    if 'pyacmegraphCmd' in config['TESTS'] :
        pyacmegraphCmd = config['TESTS']['pyacmegraphCmd']
    else:
        print("pyacmegraphCmd init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","pyacmegraphCmd" ,"INIT Value needed")
        exit()
    if 'pyacmegraphTemplate' in config['TESTS'] :
        pyacmegraphTemplate = config['TESTS']['pyacmegraphTemplate']
    else:
        print("pyacmegraphTemplate init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","pyacmegraphTemplate" ,"INIT Value needed")
        exit()
    if 'pyacmegraphShunt' in config['TESTS'] :
        pyacmegraphShunt = config['TESTS']['pyacmegraphShunt']
    else:
        print("pyacmegraphShunt init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","pyacmegraphShunt" ,"INIT Value needed")
        exit()
    if 'logFilesPath' in config['TESTS'] :
        logFilesPath = config['TESTS']['logFilesPath']
    else:
        print("logFilesPath init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","logFilesPath" ,"INIT Value needed")
        exit()
    if 'testPath' in config['TESTS'] :
        testPath = config['TESTS']['testPath']
    else:
        print("testPath init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","testPath" ,"INIT Value needed")
        exit()
    #if 'iiocatpurePath' in config['TESTS'] :
    #    iiocatpurePath = config['TESTS']['iiocatpurePath']
    #else:
    #    print("iiocatpurePath init value is needed in conf file: " + configFile)
    #    confFile.update(configFile, "TESTS","iiocatpurePath" ,"INIT Value needed")
    #    exit()
    if 'pyacmecapturePath' in config['TESTS'] :
        pyacmecapturePath = config['TESTS']['pyacmecapturePath']
    else:
        print("pyacmecapturePath init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","pyacmecapturePath" ,"INIT Value needed")
        exit()
    if 'pyacmecaptureVersion' in config['TESTS'] :
        pyacmecaptureVersion = config['TESTS']['pyacmecaptureVersion']
    else:
        try:
            #ToDo replace with subprocess.run(, capture_output=True) or subprocess.check_output("cmd", stderr=subprocess.STDOUT, shell=True)
            cmdvers = "-h | grep \"(version \" | egrep -o \"[0-9]\\.[0-9]+\""
            print("python " + pyacmecapturePath + "pyacmecapture.py " + cmdvers)
            p = subprocess.Popen("python " + os.path.join(pyacmecapturePath, "pyacmecapture.py ") + cmdvers, stdout=subprocess.PIPE, shell=True)
            out, err = p.communicate()
            pyacmecaptureVersion = out.decode("utf-8").rstrip()
        except:
            pyacmecaptureVersion = "default"
    print("pyacmecaptureVersion= " + pyacmecaptureVersion)

    if 'pyacmecaptureSlots' in config['TESTS'] :
        pyacmecaptureSlots = config['TESTS']['pyacmecaptureSlots']
    else:
        try:
            cmdslots = " -s " + acmeName + " system_info | grep slot | grep -v empty | egrep -o \"slot [0-9]+\" | egrep -o \"[0-9]+\" | sed \':a;N;$!ba;s/\\n/,/g\'"
            print(os.path.join(acmecliPath , "acme-cli") + cmdslots)
            p = subprocess.Popen(os.path.join(acmecliPath , "acme-cli") + cmdslots,
                                 stdout=subprocess.PIPE, shell=True)
            out, err = p.communicate()
            pyacmecaptureSlots = out.decode("utf-8").rstrip()
        except:
            pyacmecaptureSlots = "default"
    print("pyacmecaptureSlots= " + pyacmecaptureSlots)

    if 'probeList' in config['TESTS'] :
        #probeList = config['TESTS']['probeList']
        probeList = ast.literal_eval(config.get('TESTS', 'probeList'))
    else:
        print("probeList init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","probeList" ,"INIT Value needed")
        exit()
    if 'resultsDir' in config['TESTS'] :
        resultsDir = config['TESTS']['resultsDir']
    else:
        print("resultsDir init value is needed in conf file: " + configFile)
        confFile.update(configFile, "TESTS","resultsDir" ,"INIT Value needed")
        exit()
    if 'exitOnLauncherEnd' in config['TESTS']:
        exitOnLauncherEnd = config['TESTS']['exitOnLauncherEnd']
    else:
        exitOnLauncherEnd = "False"
    # Initialisations necessary for test launcher with tempbench disabled
    tempFineTune = False
    warmUpAuto = False
    TFTDuration = str(0)
    if "tempDieTarget" in config['TEMPBENCH']:
        tempbench = True
        print("++++++++++TEST LAUNCHER + TEMPBENCH ENABLED for temp control++++++++++")
        if 'warmUpTest' in config['TEMPBENCH']:
            warmUpTest = config['TEMPBENCH']['warmUpTest']
        else:
            print("warmUpTest init value is needed in conf file: " + configFile)
            confFile.update(configFile, "TEMPBENCH","warmUpTest" ,"INIT Value needed")
            exit()
        if 'warmUpAuto' in config['TEMPBENCH'] :
            warmUpAuto = config['TEMPBENCH']['warmUpAuto']
        if 'rebootAfterWarmUp' in config['TEMPBENCH']:
            rebootAfterWarmUp = config['TEMPBENCH']['rebootAfterWarmUp']
        if 'maxBootTemp' in config['TEMPBENCH'] :
            maxBootTemp = config['TEMPBENCH']['maxBootTemp']
        if 'safeTemp' in config['TEMPBENCH'] :
            safeTemp = config['TEMPBENCH']['safeTemp']
        if 'tempFineTune' in config['TEMPBENCH']:
            tempFineTune = str2bool(config['TEMPBENCH']['tempFineTune'])
        #else:
        #    tempFineTune = False
        if 'TFTRamp' in config['TEMPBENCH']:
            TFTRamp = int(config['TEMPBENCH']['TFTRamp'])
        else:
            TFTRamp = 20
        if 'TFTDuration' in config['TEMPBENCH']:
            TFTDuration = config['TEMPBENCH']['TFTDuration']
        else:
            TFTDuration = str(50)
        if 'TFTMultiplier' in config['TEMPBENCH']:
            TFTMultiplier = config['TEMPBENCH']['TFTMultiplier']
        else:
            TFTMultiplier = 2
    else:
        tempbench = False
        print("----------TEST LAUNCHER EXECUTE WITH TEMPBENCH DISABLED----------")
    if 'toaddr' in config['MAIL'] :
        sendMail = True
    else:
        sendMail = False
    if 'onoffbox' in config['TESTS']:
        onoffbox = config['TESTS']['onoffbox']
    else:
        onoffbox = onoffbox_default

    if acmegraph:
        pyacmegraph = pyacmegraphCmd + " --ip " + acmeName + " --template " + pyacmegraphTemplate + " " + pyacmegraphShunt + " &"
        print ('>>>>>>> pyacmegraph = ' + pyacmegraph)
        ret = subprocess.call(pyacmegraph, shell=True)
        print("subprocess return:" + str(ret))

    if tempbench:
        maxTFTDuration = int(float(TFTMultiplier)) * int(float(TFTDuration))
        testTFTduration = str(int(float(testDuration)) + int(float(TFTDuration)))
        maxDuration = int(float(testDuration)) + maxTFTDuration
        testTimeoutMargin = 10
        testTimeout = max(testTimeout, (maxDuration + testTimeoutMargin))

    print("testTimeout: " + str(testTimeout))

    if prepareBoard:
        thread_term_Init = startTermThread(termType, testTimeout, ser, configFile)
        thread_term_Init.threadType = "Init"
        bootBoardInit = rebootBoardOnInit(acmecliPath, acmeName, thread_term_Init,termType, bootBoardInit, onoffbox)

    if termType == "basic":
        if prepareBoard:
            thread_term_Init.join()
        if warmUpAuto == "True" :
            #To be clarified need cons_timeout > 10 to force transition ITER1. Code can hang here if value is too low
            thread_term_WarmUp = startTermThread(termType, 15, ser, configFile)
            bootBoardInit = rebootBoardOnInit(acmecliPath, acmeName, thread_term_WarmUp, termType, bootBoardInit, onoffbox)
        else:
            thread_term_Test = startTermThread(termType, testTimeout, ser, configFile)
            bootBoardInit = rebootBoardOnInit(acmecliPath, acmeName, thread_term_Test, termType, bootBoardInit, onoffbox)

    else:
        if prepareBoard:
            thread_term_Test = 	thread_term_Init
            thread_term_Init.threadType = "Test"
        else:
            thread_term_Test = startTermThread(termType, testTimeout, ser, configFile)
        bootBoardInit = rebootBoardOnInit(acmecliPath, acmeName, thread_term_Test, termType, bootBoardInit, onoffbox)

    if warmUpAuto  == "True" :
        warmUp(termType, thread_term_WarmUp)
        print("return from warmup, waiting thread to stop")
        thread_term_WarmUp.join()
        print("start test thread")
        thread_term_Test = startTermThread(termType, testTimeout, ser, configFile)
        print ("rebootAfterWarmUp = " + rebootAfterWarmUp)
        if rebootAfterWarmUp == "True" :
            print ("POST WARM UP reboot ")
            if not boardInit.rebootBoard(acmecliPath, acmeName, thread_term_Test, termType, onoffbox):
                print("ERROR: Fail multiple time to reboot after warm-up")
                exit()
        else:
            stopTest(ser)

    for testName in testList:
        if tempbench:
            peltierTemp = peltierOp.readPeltier(termType, thread_term_Test)
            #runTest(ser, testPath, testName, duration) #too intrusive affects power measurements
        thread_term_Test.logFileStatus = "NOT_READY"
        runTestNoLog(ser, testPath, testName, testDuration, TFTDuration)
        print("\n")
        if tempFineTune:
            # fine tune temperature
            time.sleep(TFTRamp)
            deltaTemp = int(float(thread_term_Test.dieTemp)) - int(float(thread_term_Test.tempDieTarget))
            thread_term_Test.tempPeltier = str(int(float(peltierTemp)) - deltaTemp)
            peltierOp.setPeltierImmediate(termType, thread_term_Test)
        if not acmegraph:
            #ToDo this depends on the temp fine tune value, clean-up needed
            maxTrial = 100
            while thread_term_Test.testStatus != "PROBE STARTED" and termType == "basic":
                time.sleep(1)
                print("waiting for probe start. current status is: " + thread_term_Test.testStatus)
                maxTrial -= 1
                if maxTrial <= 0:
                    print("Stop waiting for PROBE START")
                    break
            pyacmecaptureParam = (pyacmecapturePath, pyacmecaptureVersion, pyacmecaptureSlots)
            probePower(testName, probeList, pyacmecaptureParam, str(probeDuration), resultsDir, acmeName)

        if waitTestEnd(thread_term_Test, testName, testTimeout, ser):
            print(testName + " COMPLETED SUCCESSFULLY")
            testSuccess = True
        else:
            print(testName + " FINISHED WITH ERROR OR TIMEOUT")
            testSuccess = False
        if waitLogFile(thread_term_Test, testName):
            createTestLog(testName, ser, resultsDir)
        if (rebootOnFailure == "True" and not testSuccess) or rebootAfterEachTest == "True":
            if not boardInit.rebootBoard(acmecliPath, acmeName, thread_term_Test, termType, onoffbox):
                print("ERROR: fail multiple time to reboot after test: " + testName + " completion")
    cmd =  join(testPath, "launcherTeardown.sh")
    sendserial(cmd, ser)
    for testName in testList:
        if thread_term_Test.copyMethod == "zmodem":
            saveLog2Host(testName, ser, logFilesPath, resultsDir, thread_term_Test)
        else:
            print("no saveLog2Host method implemented for copymethod: " + thread_term_Test.copyMethod)
            print("logs available on target in directory" + thread_term_Test.boardConnectPattern[:-1] + logFilesPath)

    print('copy tools for postprocessing')
    copy_tree(join('..', 'tools'), join('..', resultsDir))
    print('create dupplicated zip file')
    resultsDirZip = resultsDir + "zip"
    print('create zip archive')
    shutil.make_archive(join('..', resultsDirZip, resultsDir), 'zip', join('..', resultsDir))

    if sendMail :
        sendMailConf.send_mail(configFile)

    if tempbench:
        thread_term_Test.tempPeltier = safeTemp
        #Safety measure set to Default Peltier Value
        peltierOp.setPeltierImmediate(termType, thread_term_Test)
    #Wait for keyboard interrupt in case of exitOnLauncherEnd == "False"
    if exitOnLauncherEnd == "True":
        print("join thread_term_Test")
        thread_term_Test.join()
        print("thread_term_Test stopped")
        exit()

    print("Press enter to go in console mode")
    #readline used for completion called from upper thread is buggy causing tty issue on program exit, no wa identified
    # recover with stty sane once back in shell
    # https://mail.python.org/pipermail/python-list/2009-October/555304.html
    #if exitOnLauncherEnd == "False":
        #startTermInst(termType, testTimeout, ser, configFile, True)
        #subprocess.call("python3 basicSerialAuto.py " + configFile, shell=True)
    #exit()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()
