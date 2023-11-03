#!/bin/bash
DIRECTORY=generators/nprc/density_benchmarks

for d in `seq -w 010 10 010`
do
	nohup /home/thinklex/newground/start_benchmark_tests.py ${DIRECTORY}/${d}_density benchmark_output_nprc_02_${d}_density &> log_nprc_02_${d}_density.log &
done
