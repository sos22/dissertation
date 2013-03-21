#! /usr/bin/env python

import os
import sys
import math

import common
import times

times.max_time = 15.

print "\\begin{tikzpicture}"

common.draw_alpha_axis()
times.draw_time_axes(5)

# Now extract the data
series = {}
for alpha in common.alphas:
    nr_timeouts = 0
    data = []
    for logfile in os.listdir("%d" % alpha):
        path = "%d/%s" % (alpha, logfile)
        l = file(path)
        line = l.readline().strip()
        w = line.split()
        if len(w) != 3 or w[0] != "buildProbeMachine":
            fail("%s doesn't start with bpm line" % path)
        if w[1:] == ["timed", "out"]:
            nr_timeouts += 1
            continue
        if w[1] != "took":
            fail("%s is not a bpm line (%s)" % (line, path))
        data.append(float(w[2]))
    data.sort()
    series[alpha] = (nr_timeouts, data)

# Plot the timeout chart
times.plot_timeout_chart(series)
times.plot_times(series, True, times.time_to_y)

print "\\end{tikzpicture}"
