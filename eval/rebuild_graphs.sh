#! /bin/sh

set -e
set -x

cd artificial_bugs
./indexed_toctou_no_scs.py > special/indexed_toctou_no_scs.tex
./indexed_toctou_vary_nr_ptrs.py enforcer > special/indexed_toctou_vary_nr_ptrs_enforcer.tex
./indexed_toctou_vary_nr_ptrs.py no_enforcer > special/indexed_toctou_vary_nr_ptrs_no_enforcer.tex
./delay_positioning.py > special/delay_positioning.tex
./multi_bugs.py > special/multi_bugs.tex
./multi_threads.py > special/multi_threads.tex
./crash_time_to_cdf.py > crash_time_cdfs.tex
./cdf1.py > cdf1.tex
cd ..

cd complex_hb
./complex_hb_build_summaries.py
./repro_times.py
cd ..

cd complex_alias
./complex_alias.py easy < easy > easy.tex
./complex_alias.py hard < hard > hard.tex
cd ..

cd dyn_convergence
./rebuild.sh
cd ..

cd phase_breakdown
./per_crashing.py
./per_interfering.py bubbles.tar per_interfering.tex
./per_interfering.py bubbles_no_w_atomic.tar per_interfering_no_w_atomic.tex
cd ..

cd alpha
for x in 10 20 30 40 50 75 100
do
    ./parse_tarball ${x}.tar ${x}.pl
done
./gen_graph.py
cd ..
