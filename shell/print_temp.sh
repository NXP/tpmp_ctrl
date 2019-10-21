#!/bin/bash
while true
do
cat /sys/devices/virtual/thermal/thermal_zone0/temp
sleep 2
done
