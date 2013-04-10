#! /usr/bin/env python

import math
import common

timeoutheight = 3.0
common.figheight = 7.0
figsep = 1

max_time = 60.0
min_time = 0.001

def time_to_y(time):
    if time < min_time:
        return 0
    elif time > max_time:
        return common.figheight
    else:
        return math.log(time / min_time) / math.log(max_time / min_time) * common.figheight

series = common.read_input()
common.preamble()
common.alpha_axis(series)

common.kde_axis(0, True, False, True, True)

# Now plot the series
for limm in [False, True]:
    for (alpha, data) in series.iteritems():
        times = []
        nr_timeouts = 0
        nr_early_out = 0
        for x in data:
            if x["early-out"]:
                nr_early_out += 1
                continue
            if x["bpm_time"] == None:
                nr_timeouts += 1
            else:
                times.append(x["bpm_time"])

        print
        print "  %%%% alpha = %d" % alpha
        common.kde_chart(0, common.alpha_to_x(alpha), nr_early_out, None, times, nr_timeouts, 0, limm)

print "\\end{tikzpicture}"
