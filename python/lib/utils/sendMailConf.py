#!/usr/bin/env python
# Copyright 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Author: Jerome NEANNE
# Mail: jerome.neanne@nxp.com
# description: Utils for automated e-mail sending

import smtplib
from os.path import join
from lib.utils import fileOp
import configparser
import ast
import six
import os

if six.PY3:
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
else:
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    from email.MIMEBase import MIMEBase
    from email import encoders

def send_mail(configFile = "../../default_config_full.ini"):

    config = configparser.ConfigParser()
    config.read(configFile)
    config.sections()

    resultsDir = config['TESTS'].get('resultsDir', '')
    zipResults = config['TESTS'].get('zipResults', '')
    tempDieTarget = config['TEMPBENCH'].get('tempDieTarget', '')
    fromaddr = config['TESTS'].get('fromaddr', 'unknown')
    toaddrList = ast.literal_eval(config['MAIL'].get('toaddr', ''))
    smtp = config['MAIL'].get('smtp', '')
    login = config['MAIL'].get('login', '')

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddrList)
    msg['Subject'] = "Test results sent automatically for " + resultsDir + " at die temperature: " + tempDieTarget

    body = "Test results attached"

    msg.attach(MIMEText(body, 'plain'))

    dirPath = join(os.getcwd(), '..')

    if zipResults == 'True' :
        dirPath = join(dirPath, resultsDir + "zip")
    else:
        dirPath = join(dirPath, resultsDir)

    fileList = fileOp.getfilelist(dirPath)

    for filename in fileList:
        attachment = open(join(dirPath, filename), "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)

    server = smtplib.SMTP(smtp, 587)
    server.starttls()
    server.login(fromaddr, login)
    server.sendmail(fromaddr, toaddrList, msg.as_string())
    server.quit()

