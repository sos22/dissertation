#! /usr/bin/env python

from util import *
import util

util.fig_width = 14
util.abscissae = [0.1,0.15,0.2,0.3,0.45,0.7,1]
util.max_time = 1.18

print_preamble()

series = [("special/multi_bugs.crash_times_data", "No enforcer"),
          ("special/multi_bugs.0.crash_times_data", "Enforce simple\_toctou only"),
          ("special/multi_bugs.1.crash_times_data", "Enforce write\_to\_read only"),
          ("special/multi_bugs.both.crash_times_data", "Enforce both bugs")]

for i in xrange(len(series)):
    s = read_series(series[i][0])
    plot_series(s[0], i)
print "\\end{tikzpicture}\\\\"

print "\\centerline{"
print "\\begin{tabular}{lll}"
def do_one(idx, description):
    print "  \\raisebox{1mm}{\\tikz{\\draw%s (0,0) -- (1,0);}} %s" % (decorations[idx % len(decorations)], description)
do_one(0, series[0][1])
print " & ",
do_one(1, series[1][1])
print "  \\\\"
do_one(2, series[2][1])
print " &  ",
do_one(3, series[3][1])
print "  \\\\"
print "\\end{tabular}"
print "}"
print "\\vspace{-15pt}"
