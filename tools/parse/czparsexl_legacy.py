#!/usr/bin/env python3
import re


rails = ["VBAT", "VDD_ARM", "VDD_SOC", "VDD_DRAM", "NVCC_DRAM", "VDD_1V8", "GPU", "VPU"]
files = ["coremarkRef_time.sh_pwr.txt", "coremark3Core_time.sh_pwr.txt", "coremark2Core_time.sh_pwr.txt", "coremark1Core_time.sh_pwr.txt", "gls_buildings_time.sh_pwr.txt", "gls_boxfold_time.sh_pwr.txt", "gls_pacman_time.sh_pwr.txt","gls_bouncingspheres_time.sh_pwr.txt","gls_flags_time.sh_pwr.txt"]
units = ["(mV)", "(mA)", "(uW)"]
# Open file as file object and read to string
#ifile = open("coremarkRef_time.sh_pwr.txt",'r')
file_out = open("gnupwr.txt","w")
file_out.write('rail(unit)\t')
for rail in rails:
    for unit in units:
        file_out.write(rail + unit + "\t")
file_out.write('\n')
for filename in files:
    # Read file object to string
    ifile = open(filename,'r')
    text = ifile.read()

    # Close file object
    ifile.close()

    file_out.write(filename[:-16] + "\t")
    for rail in rails:
        rail_regex = r'('+ rail+ ').*\\n.*Voltage[\s]\(mV\):[\s]min=[-]?[0-9]*[\s]max=[-]?[0-9]*[\s]avg=[-]?([0-9]*)\\n.*Current[\s]\(mA\):[\s]min=[-]?[0-9]*[\s]max=[-]?[0-9]*[\s]avg=[-]?([0-9]*)\\n.*Power[\s]+\(uW\):[\s]min=[-]?[0-9]*[\s]max=[-]?[0-9]*[\s]avg=[-]?([0-9]*)'
        #print(rail_regex)
        pattern_meas = re.compile(rail_regex, re.VERBOSE | re.MULTILINE)

        #file_out = open("xlpwr.txt","w")
        for match in pattern_meas.finditer(text):
            output = "%s\t %s\t %s\t" % (match.group(2), match.group(3), match.group(4))
            file_out.write(output)
    file_out.write('\n')
file_out.close()
