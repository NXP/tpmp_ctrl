#!/bin/bash
echo "enter test teardown"
pkill print_temp_time
pkill QX_coremark_run
pkill coremark_4.exe
ps
echo "-------------------TEST END----------------------------"
