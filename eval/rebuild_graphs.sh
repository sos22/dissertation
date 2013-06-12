#! /bin/sh

set -e
set -x

cd artificial_bugs
# ./indexed_toctou_no_scs.py > special/indexed_toctou_no_scs.tex
# ./indexed_toctou_vary_nr_ptrs.py enforcer > special/indexed_toctou_vary_nr_ptrs_enforcer.tex
# ./indexed_toctou_vary_nr_ptrs.py no_enforcer > special/indexed_toctou_vary_nr_ptrs_no_enforcer.tex
# ./delay_positioning.py > special/delay_positioning.tex
# ./multi_bugs.py > special/multi_bugs.tex
# ./multi_threads.py > special/multi_threads.tex
# ./crash_time_to_cdf.py > crash_time_cdfs.tex
# ./cdf1.py > cdf1.tex
cd ..

cd complex_hb
#./complex_hb_build_summaries.py > complex_hb_build_summaries.tex
cd ..

cd complex_alias
# ./complex_alias.py easy < easy > complex_alias_easy.tex
# ./complex_alias.py hard < hard > complex_alias_hard.tex
cd ..

cd alpha
cd unopt
#../build_bpm_graph.py > bpm.tex
#../build_gsc_graph.py > gsc.tex
#../build_gvc_graph.py > gvc.tex
#../build_crashing_size_graph.py > crashing_size.tex
cd ..

cd opt
# ../build_bpm_graph.py > bpm.tex
# ../build_gsc_graph.py opt > gsc.tex
# ../build_gvc_graph.py > gvc.tex
# ../build_crashing_size_graph.py > crashing_size.tex
cd ..
cd ..

cd bubble_charts
# ./rebuild.sh
cd ..
