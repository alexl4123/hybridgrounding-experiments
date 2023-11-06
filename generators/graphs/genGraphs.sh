FOLDER=S3-T4
mkdir ./$FOLDER

cp ./encodings/${FOLDER}_hg_encoding.lp ./$FOLDER/hg_encoding.lp
cp ./encodings/${FOLDER}_traditional_encoding.lp ./$FOLDER/traditional_encoding.lp

for prob in `seq -w 010 10 030` 
do
    mkdir ./$FOLDER/$prob
	for vertices in `seq -w 010 10 100`
	do
        mkdir ./$FOLDER/$prob/$vertices

        for k in `seq -w 01 1 10`
        do
            seed=$RANDOM
            echo "size $vertices, prob $prob, repetition $k, seed $seed"
            python3 genGraph.py $vertices $prob $seed $k > ./$FOLDER/$prob/$vertices/$k.lp
        done
	done
done

