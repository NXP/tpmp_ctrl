#!/bin/bash
duration=$1
uname -a
echo "BoardID: "
/unit_tests/memtool -32 0x3035C410 1
/unit_tests/memtool -32 0x3035C420 1
/unit_tests/autotest/OPP-setup.sh
echo "CPU0 online: "
cat /sys/devices/system/cpu/cpu0/online
echo "CPU1 online: "
cat /sys/devices/system/cpu/cpu1/online
echo "CPU2 online: "
cat /sys/devices/system/cpu/cpu2/online
echo "CPU3 online: "
cat /sys/devices/system/cpu/cpu3/online
echo "scaling_cur_freq"
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq
echo "scaling_available_frequencies"
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies
echo "clk_summary"
cat /sys/kernel/debug/clk/clk_summary
echo "-------------------TEST start: $0 ----------------------------"
cd /unit_tests/Benchmarks;
#/unit_tests/Benchmark/glslsandbox-player.fb -S BoxFold -t $duration -D &
/unit_tests/Benchmarks/glslsandbox-player.fb -S BoxFold -t $duration &
ps
echo "-------------------FINE ADJUST TEMP----------------------------"
/unit_tests/autotest/print_temp_time_s.sh 50 2
echo "-------------------POWER PROBE Start: $0 ----------------------------"
/unit_tests/autotest/print_temp_time_s.sh $duration 2
echo "-------------------POWER PROBE End: $0 ----------------------------"
/unit_tests/autotest/teardownGLS.sh
cd /unit_tests/autotest;

