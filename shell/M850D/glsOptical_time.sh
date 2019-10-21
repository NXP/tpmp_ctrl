#!/bin/bash
duration=$1
echo "-------------------TEST start: $0 ----------------------------"
cd /unit_tests/Benchmarks;
#/unit_tests/Benchmarks/glslsandbox-player.fb -S OpticalCircuit -t $duration -D &
/unit_tests/Benchmarks/glslsandbox-player.fb -S OpticalCircuit -t $duration &
echo "-------------------POWER PROBE Start: $0 ----------------------------"
/unit_tests/autotest/print_temp_time_s.sh $duration 2
echo "-------------------POWER PROBE End: $0 ----------------------------"
/unit_tests/autotest/teardownGLS.sh
cd /unit_tests/autotest;

