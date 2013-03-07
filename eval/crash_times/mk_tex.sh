#! /usr/bin/env bash

set -e

base=${1/.tex}
t=$(mktemp)
cat > $t <<EOF
set terminal latex
set output "${base}.tex"
set logscale x
plot '${base}__enforcer.cdf' with lines title "With enforcer", '${base}__no_enforcer.cdf' with lines linestyle 3 title "Without enforcer"
EOF
gnuplot $t
rm -f $t
