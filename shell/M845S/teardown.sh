#!/bin/bash
echo "enter test teardown"
pkill print_temp.sh
pkill print_temp_time
pkill print_time
pkill gplay-1.0
pkill gst-launch-1.0
pkill memtest.arm
pkill coremarkRef_time.sh
sleep 1
pkill coremark_4.exe
ps
echo "-------------------TEST END----------------------------"
