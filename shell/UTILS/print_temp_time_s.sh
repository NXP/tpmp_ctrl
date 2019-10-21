#!/bin/bash
counter=$1
printdelay=$2
counter=$(($counter / $printdelay))
while [ $counter -gt 0 ]
do
#echo -n "Die Temperature: "
#cat /sys/devices/virtual/thermal/thermal_zone0/temp
DIETEMP=$(cat /sys/devices/virtual/thermal/thermal_zone0/temp)
echo "Die Temperature: $DIETEMP"
sleep $printdelay
counter=$(( $counter - 1 ))
timeleft=$(($counter * $printdelay))
echo "test finished in $timeleft sec"
done
