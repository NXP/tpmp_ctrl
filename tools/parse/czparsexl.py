#!/usr/bin/env python3
import re

rails = ["VBAT", "VDD_ARM", "VDD_SOC", "VDD_DRAM", "NVCC_DRAM", "VDD_1V8", "GPU", "VPU"]
files = ["coremarkRef_time.sh-report.txt", "coremark3Core_time.sh-report.txt", "coremark2Core_time.sh-report.txt", "coremark1Core_time.sh-report.txt", "gls_buildings_time.sh-report.txt", "gls_boxfold_time.sh-report.txt", "gls_pacman_time.sh-report.txt","gls_bouncingspheres_time.sh-report.txt","gls_flags_time.sh-report.txt"]
units = ["(mV)", "(mA)", "(mW)"]
file_out = open("gnupwr.txt","w")
file_out.write('rail(unit)\t')
for rail in rails:
    for unit in units:
        file_out.write(rail + unit + "\t")
file_out.write('\n')
for filename in files:
    outputList = []
    # Read file object to string
    ifile = open(filename,'r')
    text = ifile.read()

    # Close file object
    ifile.close()

    file_out.write(filename[:-19] + "\t")
    volt_regex = r'(Voltage[\s]*[\n].*[\n].*[\n][\s]Avg[\s]\(mV\)[\s]+(.*))'
    volt_meas = re.compile(volt_regex, re.VERBOSE | re.MULTILINE)
    for match in volt_meas.finditer(text):
        volt_output = "%s" % (match.group(2))
        #print(volt_output)
    cur_regex = r'(Current[\s]*[\n].*[\n].*[\n][\s]Avg[\s]\(mA\)[\s]+(.*))'
    cur_meas = re.compile(cur_regex, re.VERBOSE | re.MULTILINE)
    for match in cur_meas.finditer(text):
        cur_output = "%s" % (match.group(2))
        #print(cur_output)
    pwr_regex = r'(Power[\s]*[\n].*[\n].*[\n][\s]Avg[\s]\(mW\)[\s]+(.*))'
    pwr_meas = re.compile(pwr_regex, re.VERBOSE | re.MULTILINE)
    for match in pwr_meas.finditer(text):
        pwr_output = "%s" % (match.group(2))
        #print(pwr_output)
    pwr_regex = r'(Power[\n].*[\n].*[\n][\s]Avg[\s]\(mW\)[\s]+(.*))'
    volt = volt_output.split()
    cur = cur_output.split()
    pwr = pwr_output.split()
    #print(volt)
    for i in range(len(rails)):
        outputList.append(str(abs(float(volt[i]))))
        outputList.append(str(abs(float(cur[i]))))
        outputList.append(str(abs(float(pwr[i]))))
        #print(volt[i])
    print(outputList)
    for value in outputList:
        file_out.write(value + '\t')
    file_out.write("\n")
file_out.close()
