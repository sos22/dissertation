#! /usr/bin/env python

import sys
import math

decorations = ["", "[dashed]", "[dotted]"]
def fail(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)

def render_nr(t):
    if t == 0:
        return "0"
    nr_digits = int(math.log(t) / math.log(10))
    natural_max = float(10 ** nr_digits)
    first_digit = int(t/natural_max)
    if nr_digits < -4 or nr_digits > 4:
        return "$%d {\\times} 10^{%d}$" % (first_digit, nr_digits)
    elif nr_digits >= 0:
        return ("%d" % first_digit) + "0" * nr_digits
    else:
        return "0." + ("0" * (-nr_digits - 1)) + ("%d" % first_digit)

def round_up(t):
    nr_digits = int(math.log(t) / math.log(10)) + 1
    natural_max = float(10 ** nr_digits)
    if t / natural_max > 0.8:
        return (natural_max, natural_max / 10)
    first_digit = int(10 * t/natural_max) + 1
    return (first_digit * float(10 ** (nr_digits - 1)), natural_max/10)

def print_preamble():
    print "\\begin{tikzpicture}"

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

def perc_to_y(p):
    return (p * 5.0)
def time_to_x(t):
    return math.log(t/0.1) * 6.0 / math.log(1800.0)

def read_series(test_name, name):
    f = file("%s%s" % (test_name, name), "r")
    nr_timeouts = 0
    times = []
    for l in f:
        if l.strip()[-1] == "T":
            nr_timeouts += 1
        else:
            times.append(float(l.strip()))
    times.sort()
    t = []
    for i in xrange(len(times)):
        t.append( (times[i], float(i)/(len(times) + nr_timeouts - 1)) )
    return (t, nr_timeouts)

def draw_one_test(test_name):
    print_preamble()
    # Draw axes
    print "  \\draw[->] (0,0) -- (0,5);"
    print "  \\draw[->] (0,0) -- (%f,0);" % time_to_x(180)
    # x ticks
    for i in [0.1,0.5,1,2,4,8,16,32,64,180]:
        print "  \\node at (%f,0) [below] {%s};" % (time_to_x(i), i)
    # y ticks
    for i in xrange(0,11,2):
        print "  \\node at (0,%f) [left] {%s\\%%};" % (perc_to_y(i/10.0), render_nr(i* 10.0))
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
           "complex_hb_17", "multi_threads", "glibc",
           "glibc"]
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
