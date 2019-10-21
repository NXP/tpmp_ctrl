#!/bin/bash
timer=$1
printdelay=2
= / 2
while [ -gt 0 ]
do
cat /sys/devices/virtual/thermal/thermal_zone0/temp
sleep $printdelay
timer=-1
done
