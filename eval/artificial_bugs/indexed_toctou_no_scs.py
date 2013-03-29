#! /usr/bin/env python

from util import *
import util
util.fig_width = 14

def latex_escape(x):
    return x.replace("_", "\\_")

print_preamble()
series = [("indexed_toctou.crash_times_data", "No enforcer"),
          ("indexed_toctou~0.crash_times_data", "Full enforcer"),
          ("special/indexed_toctou_no_scs.crash_times_data", "No side conditions")]
for i in xrange(len(series)):
    s = read_series(series[i][0])
    plot_series(s[0], i)

print "\\end{tikzpicture}\\\\"

print "\\centerline{"
print "  {\\hfill}"
def do_one(idx, description):
    print "  \\raisebox{1mm}{\\tikz{\\draw%s (0,0) -- (1,0);}} %s" % (decorations[idx % len(decorations)], description)
do_one(0, series[0][1])
print "  {\\hfill}"
do_one(1, series[1][1])
print "  {\\hfill}"
do_one(2, series[2][1])
print "  {\\hfill}"
print "}"
print "\\vspace{-15pt}"
