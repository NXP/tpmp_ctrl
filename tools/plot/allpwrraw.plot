#
# call script ex: gnuplot -c plot/allpwrraw.plot coremarkRef
#  gnuplot -c plot/allpwrraw.plot ARG1 ARG2
# ARG1: test_name
# ARG2: probe Optional (default=pwr) current/voltage/power
# change probe on the fly press r (replot) then 2 for voltage, 3 for current 4 for power
voltage = 2
current = 3
power = 4

probeName="power" #default
probe = power
#if (ARG2 == current) probe=current
#if (ARG2 == voltage) probe=voltage
if (ARG2 == 3) probe=3
if (probe == 3) probeName="current"
if (ARG2 == 2) probe=2
if (probe == 2) probeName="voltage"

bind r "unset ylabel; \
    unset title; replot"
bind "2"      "probe = 2"
bind "3"      "probe = 3"
bind "4"      "probe = 4"

set title \
    probeName." profile per rail\n" \
    . "no filter \n"
set key invert box center right reverse Left
set xtics nomirror
set ytics nomirror
set border 3
set size 1,1
set xlabel "nsec"
if (probe == power) set ylabel "mW"
if (probe == voltage) set ylabel "mV"
if (probe == current) set ylabel "uA"

print "     @ARG1 scenario = ", ARG1
scenario = ARG1


#
# Plot data
#

datafileVBAT = scenario.'_time.sh_VBAT.csv'
datafileARM = scenario.'_time.sh_VDD_ARM.csv'
datafileVDDSOC = scenario.'_time.sh_VDD_SOC.csv'
datafileVDDDRAM = scenario.'_time.sh_VDD_DRAM.csv'
datafileNVCCDRAM = scenario.'_time.sh_NVCC_DRAM.csv'
datafileVDD1V8 = scenario.'_time.sh_VDD_1V8.csv'
datafileGPU = scenario.'_time.sh_GPU.csv'
datafileVPU = scenario.'_time.sh_VPU.csv'


set style data linespoints

plot \
     datafileVBAT using 1:probe title 'VBAT' lw 2 lc rgb 'web-blue', \
     datafileARM using 1:probe title 'ARM' lw 2 lc rgb 'orange', \
     datafileVDDSOC using 1:probe title 'SOC' lw 2 lc rgb 'green', \
     datafileVDDDRAM using 1:probe title 'VDD_DRAM' lw 2 lc rgb 'magenta', \
     datafileNVCCDRAM using 1:probe title 'NVCC_DRAM' lw 2 lc rgb 'blue', \
     datafileVDD1V8 using 1:probe title 'VDD_1V8' lw 2 lc rgb 'brown', \
     datafileGPU using 1:probe title 'GPU' lw 2 lc rgb 'yellow', \
     datafileVPU using 1:probe title 'VPU' lw 2 lc rgb 'red',

pause -1 "Hit return to continue"

reset
