#!/bin/bash
cpufreq-set -g userspace
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cpufreq-set -f 500000
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
