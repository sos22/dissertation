#! /usr/bin/env python

from util import *
import util

def latex_escape(x):
    return x.replace("_", "\\_")

for bug in ["crash_indexed_toctou", "interfering_indexed_toctou"]:
    print "\\subfigure[][%s]{" % latex_escape(bug)
    print_preamble()
    series = [("%s~0.crash_times_data" % bug, "Normal delay placement"),
              ("special/%s.delay_send.crash_times_data" % bug, "Delay on send"),
              ("special/%s.delay_recv.crash_times_data" % bug, "Delay on receive"),
              ("special/%s.delay_both.crash_times_data" % bug, "Both delays")]
    for i in xrange(len(series)):
        s = read_series(series[i][0])
        plot_series(s[0], i)
    print "\\end{tikzpicture}"
    print "\\label{fig:eval:delay_positioning:%s}" % bug
    print "}"

print "\\centerline{"
print "\\begin{tabular}{p{%fcm}p{%fcm}}" % (util.fig_width, util.fig_width)
def do_one(idx, description):
    print "\\raisebox{1mm}{\\tikz{\\draw%s (0,0) -- (0.5,0);}} %s" % (decorations[idx % len(decorations)], description),
do_one(0, series[0][1])
print " & ",
do_one(1, series[1][1])
print "\\\\"
do_one(2, series[2][1])
print " & ",
do_one(3, series[3][1])
print "\\"
print "\\end{tabular}"
print "}"
