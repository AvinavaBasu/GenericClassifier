INP_DIR=/home/a.sehgal/a.sehgal/IP2.1/Generic_Classifier/ver4/gc/input
OUT_DIR=/home/m.le/generic-classifier/output/linear_hybrid_classifiers
rm -rf $OUT_DIR
mkdir -p $OUT_DIR

run() {
    time python3 -u processTaggedAffils.py --model_path=output/$1.pkl $2 $3 2>&1 | tee $3.log
}

for model in hybrid_classifier-linear hybrid_classifier-linear-weighted hybrid_classifier-linear-weighted-multiling
do
    for fname in ani.cec.train.hi.xml ani.supp.train.hi.xml ani.train.hi.xml grants.train.hi.xml medline.train.hi.xml
    do
        inp=$INP_DIR/$fname
        out=$OUT_DIR/$model-$fname
        run $model $inp $out
    done;
done;