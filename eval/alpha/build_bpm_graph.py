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

print "  %% Y axis"
print "  \\draw[->] (0,0) -- (0,%f);" % common.figheight
for t in ["0.001", "0.01", "0.1", "1", "10", "60"]:
    print "  \\node at (0,%f) [left] {%s};" % (time_to_y(float(t)), t)
    print "  \\draw [color=black!10] (0,%f) -- (%f,%f);" % (time_to_y(float(t)), common.figwidth, time_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {Time in seconds};" % (common.figheight / 2)

# Now plot the series
for (alpha, data) in series.iteritems():
    samples = [x["bpm_time"] for x in data]
    nr_timeouts = len([x for x in samples if x == None])
    times = [x for x in samples if x != None]
    (mean, sd) = common.mean(times)

    times += [max_time] * nr_timeouts
    print
    print "  %%%% alpha = %d" % alpha

    common.draw_box_plot(common.alpha_to_x(alpha), time_to_y, times, mean, sd)
common.box_legend(0)

# And now for the timeout rate
timeout_data = []
for (alpha, data) in series.iteritems():
    samples = [x["bpm_time"] for x in data]
    nr_timeouts = len([x for x in samples if x == None])
    nr_non_timeout = len([x for x in samples if x != None])
    timeout_data.append((alpha, float(nr_timeouts) / (nr_timeouts + nr_non_timeout)))
common.timeout_chart(common.figheight + figsep, timeoutheight, 1.0, {"": timeout_data}, 20)

print "\\end{tikzpicture}"
