#!/bin/bash
echo "enter test teardown"
pkill coremarkRef_time.sh
sleep 1
pkill coremark_4.exe
ps
echo "-------------------TEST END----------------------------"
