#!/usr/bin/env python
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Used to escape special characters before pushing file through serial

import os, sys, shutil

#ToDo: file to move or remove...

from lib.utils import fileOp

def escape(srcpath = None, dstpath = None):
    esccharlist = ["$", "#", "!", '"', "&", "(", ")", ">", "<", "*"]

    filelist = []
    if os.path.isdir(dstpath):
        shutil.rmtree(dstpath)
    os.mkdir(dstpath)

    filelist = fileOp.getfilelist(srcpath)
    for f in filelist:
        with open(srcpath + "/" + f, 'rb') as inputf:
            with open(dstpath + "/" + f, 'wb') as outputf:
                for line in inputf:
                    for escchar in esccharlist:
                        line.replace(escchar.encode(), ("\\" + escchar).encode())
                    outputf.write(line)

