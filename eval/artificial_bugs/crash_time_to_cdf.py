#! /usr/bin/env python

import sys
import math
from util import *

def print_trailer(test_name):
    print "\\end{tikzpicture}"
    print "\\label{fig:eval:crash_cdf:%s}" % test_name

def print_legend(x, series, series_keys):
    print "  \\node at (%f,0.5) [above left] {\\shortstack[l]{" % x
    f = True
    for name in series_keys:
        t = series[name]
        if not f:
            print "\\\\"
        f = False
        print "    \\raisebox{1mm}{\\tikz{\\draw%s (0,0) -- (0.5,0);}} %s" % (t[-1], name),
    print "  }};"

def draw_one_test(test_name):
    print_preamble()
    # Draw the series.
    series = [(".crash_times_data", "No enforcer"),
              ("~0.crash_times_data", "Enforcer"),
              ("~0.dc.crash_times_data", "Data collider")]
    i = 0
    for (fname, _descr) in series:
        s = read_series(test_name, fname)
        print "  \\draw%s (0,0) " % decorations[i % len(decorations)],
        last_y = 0
        for (x,y) in s[0]:
            last_y = y
            if x < 0.1:
                x = 0.1
            lp = "(%f,%f)" % (time_to_x(x), perc_to_y(y))
            print " -- %s" % lp,
        print " -- (%f, %f);" % (time_to_x(180), perc_to_y(last_y))
        i += 1

    print_trailer(test_name)

legend = "Cumulative distribution functions of the time taken by the test cases to crash.  Solid lines show time without an enforcer; dashed lines show time with an enforcer; dotted lines show time with the DataCollider-like tool.  All tests were run 100 times with a 180 second timeout.  Note log scale."

buglist = ["simple_toctou", "indexed_toctou", "crash_indexed_toctou",
           "interfering_indexed_toctou", "context", "cross_function",
           "double_free", "multi_variable", "write_to_read",
           "broken_publish", "complex_hb_5", "complex_hb_11",
           "complex_hb_17", "multi_threads", "glibc"]
print "\\newcounter{fnarkedsubfigure}"
print "\\setcounter{fnarkedsubfigure}{0}"
def do_figure(bugs, is_last = False):
    print "\\begin{figure}"
    print "\\setcounter{subfigure}{\\value{fnarkedsubfigure}}"
    for x in bugs:
        test_descrs = { "complex_hb_5": "$\\textrm{complex\\_hb}_5$",
                        "complex_hb_11": "$\\textrm{complex\\_hb}_{11}$",
                        "complex_hb_17": "$\\textrm{complex\\_hb}_{17}$" }
        def latex_escape(what):
            return what.replace("_", "\\_")
        print "\\subfigure[][%s]{" % test_descrs.get(x, latex_escape(x))
        draw_one_test(x)
        print "}"
    print "\\setcounter{fnarkedsubfigure}{\\value{subfigure}}"
    print "\\subfigure{"
    print "\\hspace{5mm}\\raisebox{3cm}{\\parbox{7cm}{%s}}" % legend
    print "}"
    print "\\caption{}"
    if is_last:
        print "\\label{fig:eval:summary_cdfs}"
    print "\\end{figure}"
    print "\\addtocounter{figure}{-1}"
do_figure(buglist[0:5])
do_figure(buglist[5:10])
do_figure(buglist[10:15], True)

print "\\addtocounter{figure}{1}"
