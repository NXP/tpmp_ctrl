#!/usr/bin/env python
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Utils for file management and copy over serial

import os, sys, shutil
from os.path import isfile, join, isdir
import six
from subprocess import call
import subprocess
import hashlib

def getfromterm(txt):
    sys.stderr.write('\n--- ' + txt + ': ')
    sys.stderr.flush()
    return sys.stdin.readline().rstrip('\r\n')

def getdirpath(txt):
    dirpath = getfromterm(txt)
    while not isdir(dirpath):
        print(dirpath + " is not a directory")
        dirpath = getfromterm(txt)
    return dirpath

def getfilelist(fpath):
    return [f for f in os.listdir(fpath) if isfile(join(fpath, f))]

def getdirlist(fpath):
    return [d for d in os.listdir(fpath) if isdir(join(fpath, d))]

def copy_dir(objInst, srcpath, dstpath):
    """Ask user for filenname and copy in local file"""
    filelist = []
    filelist = getfilelist(srcpath)
    dirlist = getdirlist(srcpath)
    for f in filelist:
        objInst.copy_file(objInst, f, srcpath, dstpath) #ToDo: clean up architecture (dependency between fileop.py and basicSerialAuto.py)
    return dirlist

def copy_subdirs(objInst, d):
    print("create subdir:" + d)
    objInst.cmdwriter("mkdir " + d ,1)

def copy_file_line(line, objInst, dstpath, filename):
    block = str(line).rstrip("\r\n")
    if not block:
        return False
    objInst.serial.write(b"echo " + block.encode() + b" >> " + join(dstpath, filename).encode() + b"\n")                             # Wait for output buffer to drain.
    objInst.serial.flush()
    sys.stderr.write('.')   # Progress indicator.
    return True

#ToDo: move to basicSerialAuto.py?
def copy_file(objInst,filename, srcpath, dstpath = "."):
    """Ask user for filenname and copy in local file"""
    srcfile = join(srcpath, filename)
    try:
        with open(srcfile, 'rb') as f:
            sys.stderr.write('--- Sending file {} ---\n'.format(srcfile))
            objInst.serial.write(b"rm " + filename.encode() + b"\n")
            for line in f:
                if six.PY3:
                    if not copy_file_line(line.decode(), objInst, dstpath, filename):
                        break
                else:
                    if not copy_file_line(line, objInst, dstpath, filename):
                        break
            sys.stderr.write('\n--- File {} sent ---\n'.format(srcfile))
    except IOError as e:
        sys.stderr.write('--- ERROR opening file {}: {} ---\n'.format(filename, e))

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def copy_execfile(objInst, filename, srcpath, dstpath = ".", tmppath = "../tmp_shell"):
    """Ask user for filenname and copy in local file"""
    srcfile = join(srcpath, filename)
    convtxtfile = join(tmppath, filename)
    md5ref = md5(srcfile.encode())
    #shell macro does not work in that python context
    #subprocess.call("function s64() { cat $1 | base64 > " + convtxtfile + "; }",shell=True)
    #subprocess.call("s64 " + srcfile + "\n",shell=True)
    objInst.serial.write(b"rm " + filename.encode()+ b"_dec\n")
    objInst.serial.flush()
    subprocess.call("cat " + srcfile + " | base64 > " + convtxtfile, shell=True)
    copy_file(objInst, filename, tmppath)
    objInst.serial.write(b"cat  " + filename.encode() + b" | base64 -d > " + filename.encode() + b"_dec\n")
    objInst.serial.write(b"mv " + filename.encode() + b"_dec " + filename.encode() + b"\n")
    objInst.serial.write(b"echo md5 ref host= " + md5ref.encode() + b"\n")
    objInst.serial.write(b"MD5REF=\"" + md5ref.encode() + b"\"\n")
    objInst.serial.write(b"md5sum " + filename.encode() + b"\n")
    objInst.serial.write(b"MD5CP=($(md5sum " + filename.encode() + b"))\n")
    objInst.serial.write(b"[[ \"$MD5CP\" == \"$MD5REF\" ]] && echo checksum Match\n") #ToDo: Display error if mismatch

def getfilepath():
    fpath = getdirpath("Path of File to copy")
    fname = getfromterm("File Name to copy")
    while not isfile(join(fpath, fname)):
        print("No file named " + fname + " in directory: " + fpath)
        fname = getfromterm("File Name to copy")
    return fname, fpath

def copy_file_term(objInst):
    """Ask user for filenname and copy in local file"""
    filename, srcpath = getfilepath()
    copy_file(objInst, filename, srcpath)

def copy_execfile_term(objInst):
    """Ask user for filenname and copy in local file"""
    filename, srcpath = getfilepath()
    copy_execfile(objInst,filename, srcpath)

def copy_tree_term(objInst, srcpath = "nopath", dstpath = "."):
    """Ask user for dir and copy in local file including subdirs"""
    if srcpath == "nopath":
        srcpath = getdirpath("Path of dir to copy")
    dirlist = copy_dir(objInst, srcpath, dstpath)
    if len(dirlist) > 0:
        for d in dirlist:
            copy_subdirs(objInst, join(dstpath, d))
            copy_tree_term(objInst, join(srcpath, d), join(dstpath, d))

    objInst.serial.flush()
    print("copy tree completed")

def rzmodem(objInst, filename, srcpath, dstpath = "."):
    """Ask user for filenname and copy in local file"""
    srcfile = join(srcpath, filename)

    objInst.cmdwriter("cd " + dstpath ,1)
    sys.stderr.write('--- Receiving file from host {} ---\n'.format(srcfile))

    call("sz " + srcfile + " > " + str(objInst.serial.port) + " < " + str(objInst.serial.port) + "\n", shell=True)

    if objInst.dirPath == "storedDirpath not initialized":
        objInst.dirPath = objInst.boardConnectPattern[:-1]
        print("dirPath initialized with: " + objInst.dirPath)
    objInst.cmdwriter("cd " + objInst.dirPath, 1)

def rzmodem_term(objInst):
    """Ask user for filenname and copy in local file"""
    filename, srcpath = getfilepath()
    rzmodem(objInst, filename, srcpath)

def szmodem(objInst, filename, hostdir = "../fromDevice", devport = b"/dev/ttymxc1"):
    cwd = os.getcwd()
    sys.stderr.write('--- Sending file to host {} ---\n'.format(filename))

    objInst.serial.write(b"sz " + filename.encode() + b" > " + devport + b" < " + devport + b"\n")
    print(hostdir)
    if not isdir(hostdir):
        cp2def = input("defaultdir " + hostdir + " does not exist create? (y/n):")
        if cp2def in ['y','yes', 'Y','Yes', 'YES']:
            os.mkdir("../fromDevice")
        else:
            hostdir = input("enter host dir path for copy destination:")
            while not isdir(hostdir):
                validDir = input(hostdir + " does not exist create? (y/n):")
                if validDir in ['y','yes', 'Y','Yes', 'YES']:
                    os.mkdir(hostdir)
    os.chdir(hostdir)
    call("rz < " + objInst.serial.port + " > " + objInst.serial.port + "\n", shell=True)
    os.chdir(cwd)

def szmodem_term(objInst, hostdir = "../fromDevice", devport = b"/dev/ttymxc0"):
    """Ask user for filenname and copy in local file"""
    filename = getfromterm("Name of file to copy from device to host")
    szmodem(objInst, filename, hostdir, objInst.ttydev.encode())
