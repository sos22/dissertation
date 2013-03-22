#! /usr/bin/env python

import os
import sys
import math
import common
import times

series = {}
max_nr = 0
for alpha in common.alphas:
    data = []
    nr_timeouts1 = 0
    nr_timeouts2 = 0
    for logfile in os.listdir("%d" % alpha):
        path = "%d/%s" % (alpha, logfile)
        l = file(path)
        line = l.readline().strip()
        if line == "buildProbeMachine timed out":
            nr_timeouts1 += 1
            continue
        line = l.readline().strip()
        if line in ["no conflicting stores", "No conflicting stores (1775)", "No conflicting stores (1794)"]:
            data.append(0)
            continue
        if line in ["atomicSurvivalConstraint timed out", "removeAnnotations failed", "removeAnnotations timed out (1768)"]:
            nr_timeouts2 += 1
            continue
        w = line.split()
        if w[0] == "atomicSurvivalConstraint" and w[1] == "took":
            line = l.readline().strip()
            if line == "getStoreCFGs timed out":
                nr_timeouts2 += 1
                continue
            w = line.split()
            if w[0] == "getStoreCFGs" and w[1] == "took":
                item = int(w[-1])
                if item > max_nr:
                    max_nr = item
                data.append(item)
                continue
            common.fail("%s: Bad GSC line %s" % (path, line))
        common.fail("%s: Bad ASC line %s" % (path, line))
    data.sort()
    series[alpha] = (nr_timeouts1, data, nr_timeouts2)

max_nr = 12
def nr_to_y(nr):
    return nr / float(max_nr) * times.height1

def print_legend(x, y, descriptions):
    print "  \\node at (%f,%f) [above left] {\\shortstack[l]{" % (x, y)
    for idx in xrange(len(descriptions)):
        if idx != 0:
            print "\\\\"
        print "    \\raisebox{1mm}{\\tikz{\\draw%s (0,0) -- (0.5,0);}} %s" % (common.decoration(idx), descriptions[idx]),
    print "  }};"

print "\\begin{tikzpicture}"
common.draw_alpha_axis()
times.draw_timeout_axis()
print "  \\draw[->] (0,0) -- (0,%f);" % (times.height1)
for p in xrange(0, max_nr+1):
    y = nr_to_y(p)
    print "  \\node at (0,%f) [left] {%d};" % (y, p)
    print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (y, common.width, y)
print "  \\node at (0,%f) [rotate=90, left = 1,anchor=south] {Number of interfering CFGs};" % (times.height1 / 2)


print "  \\draw (%f,%f)" % (common.alpha_to_x(0), times.timeout_to_y(0))
for alpha in common.alphas:
    s = series[alpha]
    timeout_rate = float(s[0] + s[2]) / (s[0] + s[2] + len(s[1]))
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), times.timeout_to_y(timeout_rate))
print "        ;"
print "  \\draw (%f,%f)" % (common.alpha_to_x(0), times.timeout_to_y(0))
for alpha in common.alphas:
    s = series[alpha]
    timeout_rate = float(s[0]) / (s[0] + s[2] + len(s[1]))
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), times.timeout_to_y(timeout_rate))
print "        ;"

print "  \\node at (%f,%f) [below left] {\\shortstack[c]{Timeouts building\\\\crashing thread}};" % (common.alpha_to_x(100), times.timeout_to_y(-.1))
print "  \\draw (%f,%f) -- (%f,%f);" % (common.alpha_to_x(85), times.timeout_to_y(0.25), common.alpha_to_x(85), times.timeout_to_y(-0.1))

print "  \\node at (%f,%f) [above right] {\\shortstack[r]{Timeouts building\\\\interfering CFGs}};" % (common.alpha_to_x(0), times.timeout_to_y(.1))
print "  \\draw (%f,%f) -- (%f,%f);" % (common.alpha_to_x(45), times.timeout_to_y(0.16), common.alpha_to_x(29), times.timeout_to_y(0.3))
print "  \\draw[dotted] (%f, %f) -- (%f, %f);" % (common.alpha_to_x(45), times.timeout_to_y(0.04), common.alpha_to_x(45), times.timeout_to_y(.255))

print "  \\node at (%f,%f) [below right] {All timeouts};" % (common.alpha_to_x(29), times.timeout_to_y(.7))
print "  \\draw (%f, %f) -- (%f, %f);" % (common.alpha_to_x(63), times.timeout_to_y(.4115), common.alpha_to_x(49), times.timeout_to_y(.59))

times.include_timeouts = False
times.lines = [(times.mk_percento(0.75), "75\\%"),
               (times.mk_percento(0.90), "90\\%"),
               (times.mean, "Mean")]
times.plot_times(series, False, nr_to_y)

print_legend(common.width, 0, [x[1] for x in times.lines])

print "\\end{tikzpicture}"
