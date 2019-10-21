#!/usr/bin/env python3
import re

rails = ["VDD_VBAT", "VDD_ARM", "VDD_SOC", "VDD_GPU_", "VDD_VPU", "VDD_DRAM", "NVCC_DRAM"]
files = ["coremarkRef_time.sh-report.txt", "c-ray_time.sh-report.txt", "memset_time.sh-report.txt"]
units = ["(mV)", "(mA)", "(mW)"]
file_out = open("gnupwr.txt","w")
'''file_out.write('rail(unit)\t')
for rail in rails:
    for unit in units:
        file_out.write(rail + unit + "\t\t")
file_out.write('\n')
for rail in rails:
    for unit in units:
        file_out.write("peak\tavg\t")
file_out.write('\n')'''

for filename in files:
    file_out.write(filename[:-19] + "\n")
    file_out.write('rail(unit)\t')
    #for rail in rails:
    for unit in units:
        file_out.write(unit + "\t\t")
    file_out.write('\n\t')
    #for rail in rails:
    for unit in units:
        file_out.write("peak\tavg\t")
    file_out.write('\n')

    outputList = []
    # Read file object to string
    ifile = open(filename,'r')
    text = ifile.read()

    # Close file object
    ifile.close()

    #file_out.write(filename[:-19] + "\t")
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
    #pwr_regex = r'(Power[\n].*[\n].*[\n][\s]Avg[\s]\(mW\)[\s]+(.*))'
    volt = volt_output.split()
    cur = cur_output.split()
    pwr = pwr_output.split()
    volt_regex = r'(Voltage[\s]*[\n].*[\n][\s]Max[\s]\(mV\)[\s]+(.*))'
    volt_meas = re.compile(volt_regex, re.VERBOSE | re.MULTILINE)
    for match in volt_meas.finditer(text):
        volt_output = "%s" % (match.group(2))
        #print(volt_output)
    cur_regex = r'(Current[\s]*[\n].*[\n][\s]Max[\s]\(mA\)[\s]+(.*))'
    cur_meas = re.compile(cur_regex, re.VERBOSE | re.MULTILINE)
    for match in cur_meas.finditer(text):
        cur_output = "%s" % (match.group(2))
        #print(cur_output)
    pwr_regex = r'(Power[\s]*[\n].*[\n][\s]Max[\s]\(mW\)[\s]+(.*))'
    pwr_meas = re.compile(pwr_regex, re.VERBOSE | re.MULTILINE)
    for match in pwr_meas.finditer(text):
        pwr_output = "%s" % (match.group(2))
        #print(pwr_output)
    #pwr_regex = r'(Power[\n].*[\n].*[\n][\s]Avg[\s]\(mW\)[\s]+(.*))'
    voltMax = volt_output.split()
    curMax = cur_output.split()
    pwrMax = pwr_output.split()

    #print(volt)
    for i in range(len(rails)):
        outputList.append(rails[i])
        outputList.append("\t")
        outputList.append(str(abs(float(voltMax[i]))))
        outputList.append("\t")
        outputList.append(str(abs(float(volt[i]))))
        outputList.append("\t")
        outputList.append(str(abs(float(curMax[i]))))
        outputList.append("\t")
        outputList.append(str(abs(float(cur[i]))))
        outputList.append("\t")
        outputList.append(str(abs(float(pwrMax[i]))))
        outputList.append("\t")
        outputList.append(str(abs(float(pwr[i]))))
        outputList.append("\n")
        #print(volt[i])
    print(outputList)
    for value in outputList:
        #file_out.write(value + '\t')
        file_out.write(value)
    file_out.write("\n")
file_out.close()

file_out_filtered = open("845filtered.txt","w")
ifile = open("gnupwr.txt","r")
#text = ifile.read()
filterLines = ["VDD_VBAT"]
for line in ifile:
    findPat = False
    for pat in filterLines:
        if re.search(pat, line):
           findPat = True
    if not findPat:
        file_out_filtered.write(line)

file_out_filtered.close()

file_out_merge = open("845pwr.txt","w")
i2file = open("845filtered.txt","r")
#text = ifile.read()
mergeLines = ["VDD_GPU", "VDD_VPU", "VDD_DRAM"]
#mergeLines = ["VDD_SOC", "VDD_GPU_VPU_DRAM"]
mergename = "VDD_GPU_VPU_DRAM"

volt = 0
cur = 0
pwr = 0
voltMax = 0
curMax = 0
pwrMax = 0
mergedline = False

for line in i2file:

    findPat = False
    for pat in mergeLines:
        #mergedline = True
        if re.search(pat, line):
           findPat = True
           if findPat and pat == mergeLines[-1]:
               mergedline = True
           mergeregex = r'([\w]*[\t]([a-zA-Z0-9_\.]*)[\t]([a-zA-Z0-9_\.]*)[\t]([a-zA-Z0-9_\.]*)[\t]([a-zA-Z0-9_\.]*)[\t]([a-zA-Z0-9_\.]*)[\t]([a-zA-Z0-9_\.]*))'
           mergelines = re.compile(mergeregex, re.VERBOSE)
           for match in mergelines.finditer(line):
               voltMax = voltMax + float((match.group(2)))
               volt = volt + float((match.group(3)))
               curMax = float((match.group(4)))
               cur = float((match.group(5)))
               pwrMax = float((match.group(6)))
               pwr = float((match.group(7)))
    if mergedline:
        voltMax = voltMax/(len(mergeLines)+1)
        volt = volt/(len(mergeLines)+1)
        file_out_merge.write(mergename + "\t" + str(voltMax)+ "\t" + str(volt)+ "\t" + str(curMax)+ "\t" + str(cur)+ "\t" + str(pwrMax)+ "\t" + str(pwr) + "\n")
        volt = 0
        voltMax = 0
        mergedline = False
    if not findPat:
        file_out_merge.write(line)

file_out_merge.close()


