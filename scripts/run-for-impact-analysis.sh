set -x

INP_DIR=/home/m.le/impact-analysis-20200320/input
OUT_DIR=/home/m.le/impact-analysis-20200320/output
rm -rf $OUT_DIR
mkdir -p $OUT_DIR

run() {
    time python3 -u processForImpactAnalysis.py --model_path=output/$1.pkl $2 $3 2>&1 | tee $3.log
}

for model in hybrid_classifier-linear-weighted
do
    for fname in random-sample-affiliations-1M.tagged.postproc.tsv \
            tiered-random-sample-affiliations.tier1.postproc.tsv \
            tiered-random-sample-affiliations.tier2.postproc.tsv \
            tiered-random-sample-affiliations.tier3.postproc.tsv \
            tiered-random-sample-affiliations.tier4.postproc.tsv
    do
        inp=$INP_DIR/$fname
        out=$OUT_DIR/$model-$fname
        run $model $inp $out
    done;
done;