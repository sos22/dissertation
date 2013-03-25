#! /usr/bin/env python

import os
import sys
import math

import common
import times

times.gap = 5
common.height += 5
common.width -= 2

if sys.argv[1] == "opt":
    is_opt = True
else:
    is_opt = False

# Now extract the data
series = {}
max_vcs = 0
for alpha in common.alphas:
    nr_timeouts = 0
    nr_pairs = 0
    nr_vcs = 0
    data = []
    for logfile in os.listdir("%d" % alpha):
        path = "%d/%s" % (alpha, logfile)
        l = file(path)
        line = l.readline().strip()
        if line == "buildProbeMachine timed out":
            continue
        w = line.split()
        if len(w) != 3 or w[:2] != ["buildProbeMachine", "took"]:
            common.fail("%s doesn't start with bpm line" % path)
        line = l.readline().strip()
        if line in ["no conflicting stores", "No conflicting stores (1775)", "No conflicting stores (1794)",
                    "atomicSurvivalConstraint timed out", "removeAnnotations failed", "removeAnnotations timed out (1768)"]:
            continue
        w = line.split()
        if len(w) != 3 or w[:2] != ["atomicSurvivalConstraint", "took"]:
            common.fail("%s: wanted ASC line, got %s" % (path, line))
        line = l.readline().strip()
        if line == "getStoreCFGs timed out":
            continue
        w = line.split()
        if len(w) != 6 or w[:2] != ["getStoreCFGs", "took"] or w[3:5] != ["seconds,", "produced"]:
            common.fail("%s: wanted GSC line, got %s" % (path, line))
        nr_pairs += int(w[-1])
        while 1:
            line = l.readline()
            if line == "":
                break
            line = line.strip()
            w = line.split()
            if w[1:] == ["buildStoreMachine", "timed", "out"]:
                continue
            if w[0] == "store" and w[1] == "CFG" and w[3:] == ["single", "store", "versus", "single", "shared", "load"]:
                data.append(0)
                continue
            if len(w) != 4 or w[1] != "buildStoreMachine" or w[2] != "took":
                common.fail("%s: wanted BSM line, got %s" % (path, line))
            t = float(w[-1])
            line = l.readline().strip()
            w = line.split()
            doit = False
            if len(w) == 4 and w[0] == "localiseLoads1" and w[2] == "timed" and w[3] == "out":
                nr_timeouts += 1
            elif len(w) == 9 and w[1:8] == ["single", "store", "versus", "single",
                                            "load,", "after", "localise"]:
                doit = True
            elif len(w) == 5 and w[1:4] == ["IC", "is", "false"]:
                doit = True
            elif len(w) == 4 and w[1] == "crash" and w[2] == "impossible":
                doit = True
            elif len(w) == 4 and w[1] == "generated" and w[2] == "VC":
                doit = True
                nr_vcs += 1
            elif len(w) == 5 and w[1:] == ["IC", "atomic", "timed", "out"]:
                nr_timeouts += 1
            elif len(w) == 6 and w[1:] == ["rederive", "CI", "atomic", "timed", "out"]:
                nr_timeouts += 1
            elif len(w) == 4 and w[1:] == ["crash", "timed", "out"]:
                nr_timeouts += 1
            elif len(w) == 5 and w[1:] == ["invert", "crash", "timed", "out"]:
                nr_timeouts += 1
            elif len(w) == 5 and w[1:] == ["build", "VC", "timed", "out"]:
                nr_timeouts += 1
            else:
                common.fail("%s: expected proc line, got %s (%s)" % (path, line, str(w)))
            if doit:
                if w[-1][0] != '(' or w[-1][-1] != ')':
                    common.fail("%s: expected proc line, got %s (B)" % (path, line))
                t += float(w[-1][1:-1])
                if t > times.max_time:
                    times.max_time = t
                data.append(t)
    data.sort()
    if nr_vcs > max_vcs:
        max_vcs = nr_vcs
    series[alpha] = (nr_timeouts, data, nr_vcs, nr_pairs)

if not is_opt:
    max_vcs = 600
else:
    max_vcs = 1000

def nr_vcs_to_y(nr_vcs):
    return times.height1 + times.gap * (nr_vcs/float(max_vcs)) + 0.5
def perc_vcs_to_y(perc):
    return times.height1 + times.gap * perc + 0.5

if not is_opt:
    times.max_time = 10.
else:
    times.max_time = 30.

print "\\begin{tikzpicture}"

common.draw_alpha_axis()
times.draw_time_axes(10)
# Draw nr_vcs axes.

print "  \\draw[->] (0,%f) -- (0,%f);" % (nr_vcs_to_y(0), nr_vcs_to_y(max_vcs))
for p in xrange(0,max_vcs+1,100):
    y = nr_vcs_to_y(p)
    print "  \\node at (0,%f) [left] {%d};" % (y, p)
    print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (y, common.width, y)
print "  \\node at (0,%f) [rotate=90, left = 1,anchor=south] {\\parbox{%fcm}{\\centering Number of verification conditions (solid)}};" % ((nr_vcs_to_y(0) + nr_vcs_to_y(max_vcs)) / 2, times.gap - 1)

print "  \\draw[->] (%f,%f) -- (%f,%f);" % (common.width, perc_vcs_to_y(0), common.width, perc_vcs_to_y(1))
for p in xrange(0,101,20):
    y = perc_vcs_to_y(p/100.0)
    print "  \\node at (%f,%f) [right] {%d\\%%};" % (common.width, y, p)
print "  \\node at (%f,%f) [rotate=-90, right = 1,anchor=south] {\\parbox{%fcm}{\\centering Fraction generating verification conditions (dashed)}};" % (common.width, (perc_vcs_to_y(0) + perc_vcs_to_y(1)) / 2, times.gap - 1)

print "  \\draw[color=black!50] (0,%f) -- (%f,%f);" % (nr_vcs_to_y(0), common.width, nr_vcs_to_y(0))

times.plot_timeout_chart(series)
times.plot_times(series, True, times.time_to_y)

# Plot the number of VCs generated
print "  \\draw (%f, %f)" % (common.alpha_to_x(0), nr_vcs_to_y(0))
for alpha in common.alphas:
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), nr_vcs_to_y(series[alpha][2]))
print "        ;"
print "  \\draw[dashed] (%f, %f)" % (common.alpha_to_x(0), perc_vcs_to_y(0))
for alpha in common.alphas:
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), perc_vcs_to_y(series[alpha][2]/float(series[alpha][3])))
print "        ;"

print "\\end{tikzpicture}"
