for i in `seq 100 100 1500` 
do
	for j in `seq 10 10 100`
	do
		echo "size $i, prob $j"
		python3 genGraph.py $i $j > instances/graphs/random_${i}_${j}.lp
	done
done
