#
# call script ex: gnuplot -c plot/allpwrrawfilter.plot coremarkRef
#  gnuplot -c plot/allpwrraw.plot ARG1 ARG2
# ARG1: test_name
# ARG2: probe Optional (default=pwr) current/voltage/power
# ARG3: n= filtering window size default 10
n = 10
if (ARG3 > 1) n=ARG2
print "     filter on n samples with n= ", n

voltage = 2
current = 3
power = 4



probeName="power" #default
probe = power
#if (ARG2 == current) probe=current
#if (ARG2 == voltage) probe=voltage
if (ARG2 == 3) probe=3
if (ARG2 == 3) probeName="current"
if (ARG2 == 2) probe=2
if (ARG2 == 2) probeName="voltage"



set title \
    probeName." profile per rail\n" \
    . "mean filter on ".n." samples\n"
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

# number of points in moving average
#n = 10

# initialize the variables
do for [i=1:n] {
    eval(sprintf("back%d=0", i))
}

# build shift function (back_n = back_n-1, ..., back1=x)
shift = "("
do for [i=n:2:-1] {
    shift = sprintf("%sback%d = back%d, ", shift, i, i-1)
}
shift = shift."back1 = x)"
# uncomment the next line for a check
# print shift

# build sum function (back1 + ... + backn)
sum = "(back1"
do for [i=2:n] {
    sum = sprintf("%s+back%d", sum, i)
}
sum = sum.")"
# uncomment the next line for a check
# print sum

# define the functions like in the gnuplot demo
# use macro expansion for turning the strings into real functions
samples(x) = $0 > (n-1) ? n : ($0+1)
avg_n(x) = (shift_n(x), @sum/samples($0))
shift_n(x) = @shift

#
# Plot data, running average and cumulative average
#

datafileVBAT = scenario.'_time.sh_VBAT.csv'
datafileARM = scenario.'_time.sh_VDD_ARM.csv'
datafileVDDSOC = scenario.'_time.sh_VDD_SOC.csv'
datafileVDDDRAM = scenario.'_time.sh_VDD_DRAM.csv'
datafileNVCCDRAM = scenario.'_time.sh_NVCC_DRAM.csv'
datafileVDD1V8 = scenario.'_time.sh_VDD_1V8.csv'
datafileGPU = scenario.'_time.sh_GPU.csv'
datafileVPU = scenario.'_time.sh_VPU.csv'

#filter artifact due to filtering
set xrange [100000000:*]

set style data linespoints

#bind r "replot"


#plotARM = "datafileARM using 1:4 title 'ARM' lw 2 lc rgb 'forest-green', \"

#plot \
#     datafileARM using 1:4 title 'ARM' lw 2 lc rgb 'forest-green', \
#     '' using 1:(avg_n($4)) title "running mean for ARM over previous n points" pt 7 ps 0.5 lw 1 #lc rgb "blue", \
#     datafileVDDDRAM using 1:4 title 'VDD_DRAM' lw 2 lc rgb 'yellow', \
#     '' using 1:(avg_n($4)) title "running mean for ARM over previous n points" pt 7 ps 0.5 lw 1 #lc rgb "orange",

if (probe == power){
plot \
     datafileVBAT using 1:(avg_n($4)) title 'VBAT' lw 2 lc rgb 'web-blue', \
     datafileARM using 1:(avg_n($4)) title 'ARM' lw 2 lc rgb 'orange', \
     datafileVDDSOC using 1:(avg_n($4)) title 'SOC' lw 2 lc rgb 'green', \
     datafileVDDDRAM using 1:(avg_n($4)) title 'VDD_DRAM' lw 2 lc rgb 'magenta', \
     datafileNVCCDRAM using 1:(avg_n($4)) title 'NVCC_DRAM' lw 2 lc rgb 'blue', \
     datafileVDD1V8 using 1:(avg_n($4)) title 'VDD_1V8' lw 2 lc rgb 'brown', \
     datafileGPU using 1:(avg_n($4)) title 'GPU' lw 2 lc rgb 'yellow', \
     datafileVPU using 1:(avg_n($4)) title 'VPU' lw 2 lc rgb 'red',
}
if (probe == voltage){
plot \
     datafileVBAT using 1:(avg_n($2)) title 'VBAT' lw 2 lc rgb 'web-blue', \
     datafileARM using 1:(avg_n($2)) title 'ARM' lw 2 lc rgb 'orange', \
     datafileVDDSOC using 1:(avg_n($2)) title 'SOC' lw 2 lc rgb 'green', \
     datafileVDDDRAM using 1:(avg_n($2)) title 'VDD_DRAM' lw 2 lc rgb 'magenta', \
     datafileNVCCDRAM using 1:(avg_n($2)) title 'NVCC_DRAM' lw 2 lc rgb 'blue', \
     datafileVDD1V8 using 1:(avg_n($2)) title 'VDD_1V8' lw 2 lc rgb 'brown', \
     datafileGPU using 1:(avg_n($2)) title 'GPU' lw 2 lc rgb 'yellow', \
     datafileVPU using 1:(avg_n($2)) title 'VPU' lw 2 lc rgb 'red',
}
if (probe == current){
plot \
     datafileVBAT using 1:(avg_n($3)) title 'VBAT' lw 2 lc rgb 'web-blue', \
     datafileARM using 1:(avg_n($3)) title 'ARM' lw 2 lc rgb 'orange', \
     datafileVDDSOC using 1:(avg_n($3)) title 'SOC' lw 2 lc rgb 'green', \
     datafileVDDDRAM using 1:(avg_n($3)) title 'VDD_DRAM' lw 2 lc rgb 'magenta', \
     datafileNVCCDRAM using 1:(avg_n($3)) title 'NVCC_DRAM' lw 2 lc rgb 'blue', \
     datafileVDD1V8 using 1:(avg_n($3)) title 'VDD_1V8' lw 2 lc rgb 'brown', \
     datafileGPU using 1:(avg_n($3)) title 'GPU' lw 2 lc rgb 'yellow', \
     datafileVPU using 1:(avg_n($3)) title 'VPU' lw 2 lc rgb 'red',
}

pause -1 "Hit return to continue"

reset
