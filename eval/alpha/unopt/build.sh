#! /bin/sh

set -e
set -x

../build_bpm_graph.py unopt > bpm.tex
../build_gsc_graph.py > gsc.tex
../build_gvc_graph.py unopt > gvc.tex
