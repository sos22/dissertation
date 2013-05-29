#! /usr/bin/env python

import sys

from util import *
import util
util.fig_width = 14

print_preamble()
series = [("multi_threads.crash_times_data", "No enforcer"),
          ("multi_threads~0.crash_times_data", "Enforcer with a fair lock"),
          ("special/multi_threads_unfair.crash_times_data", "Enforcer with an unfair lock")]
i = 0
for (fname, _descr) in series:
    s = read_series(fname)
    plot_series(s[0], i)
    i += 1
print "\\end{tikzpicture}}"

print "\\centerline{"
print "{\hfill}",
def do_one(idx, description):
    print "  \\raisebox{1mm}{\\tikz{\\draw%s (0,0) -- (1,0);}} %s" % (decorations[idx % len(decorations)], description)
do_one(0, series[0][1])
print "{\hfill}",
do_one(1, series[1][1])
print "{\hfill}",
do_one(2, series[2][1])
print "{\hfill}",
print "}"
