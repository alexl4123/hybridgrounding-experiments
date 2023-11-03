#!/bin/bash
MYPATH=generators/traffic_planning_graphs/04_density_benchmarks_star

for star in 4
do
	for d in `seq -w 010 10 060`
	do
		nohup /home/thinklex/newground/start_benchmark_tests.py ${MYPATH}_${star}/${d}_density benchmark_output_tpg_04_star_${star}_${d}_density &> log_tpg_04_star_${star}_${d}_density.log &
	done
done
