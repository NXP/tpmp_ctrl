#
# Example of using histogram modes
#
reset
set title "CZ results"
#set datafile missing "-"
set xtics nomirror rotate by -45
#set key noenhanced
#set key invert reverse Left outside
#set key bottom outside
set style fill solid border -1
#set boxwidth 2
#set term x11 size 800, 400
set size 0.5,0.5
#set term pbm size 600, 400
#
# First plot using linespoints
set style data linespoints

set multiplot layout 1,3 title "report measures" font ",14"
set xtics rotate
set bmargin 5
#
set title "Power"
plot 'gnupwr.txt' using 7:xtic(1) title columnheader(7), \
for [i=1:6] '' using 7+3*i title columnheader(7+3*i)
#
set title "Current"
plot 'gnupwr.txt' using 6:xtic(1) title columnheader(6), \
for [i=1:6] '' using 6+3*i title columnheader(6+3*i)
#
set title "Voltage"
plot 'gnupwr.txt' using 5:xtic(1) title columnheader(5), \
for [i=1:6] '' using 5+3*i title columnheader(5+3*i)
#plot 'gnupwr.txt' using 4:xtic(1) title columnheader(4), \
#for [i=1:6] '' using 4+3*i title columnheader(4+3*i)
#plot 'gnupwr.txt' using 7:xtic(1) title columnheader(7), \
#for [i=1:6] '' using 7+3*i title columnheader(7+3*i)
#
pause -1 "<cr> to plot the same data as a histogram"
pause -1 "<cr> to finish histogram demo"
reset
