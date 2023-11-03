#!/bin/bash
SCRIPTPATH=/home/thinklex/newground/start_benchmark_tests.py
INSTANCESPATH=generators/traffic_planning_graphs

for star in 6
do
	for d in `seq -w 010 10 020`
	do
		nohup ${SCRIPTPATH} ${INSTANCESPATH}/03_density_benchmarks_star_${star}/${d}_density benchmark_output_tpg_03_star_${star}_${d}_density &> log_tpg_03_star_${star}_${d}_density.log &
	done
done 
