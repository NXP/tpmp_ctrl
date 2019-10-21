#!/bin/bash
duration=$1
echo "-------------------WARMUP start: $0 ----------------------------"
cd /unit_tests/autotest/kpa_coremark_scripts;
/unit_tests/autotest/kpa_coremark_scripts/QX_coremark_run.sh &
/unit_tests/autotest/print_temp_time_s.sh $duration 2
/unit_tests/autotest/teardownCM.sh
cd /unit_tests/autotest;

