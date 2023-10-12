#!/bin/bash
BASE_PATH=/home/thinklex/newground/generators/cliques/instances/


for f in ${BASE_PATH}parsed_instances/*
do
	filename=$(basename "$f")
	count=$(echo "${filename}" | grep -oP '^[\d]+')

	if (( 10#$count < 10#10000 ))
	then
		if [[ "${filename}" == *"metro+bus.gr.bz2.lp.lp.paths_tw3.lp"* ]]
		then
			echo "${filename}"
			cp $f ${BASE_PATH}used_instances/${filename}

		fi

	fi



done
