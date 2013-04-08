#! /usr/bin/env python

import os
import sys
import math
import common

common.figheight = 7.0
timeoutheight = 3
figsep = 1

max_cnt = 20.0
min_cnt = 0.0
min_time = 0.0001
max_time = 60

def count_to_y(cnt):
    if cnt <= min_cnt:
        return 0
    elif cnt > max_cnt:
        return common.figheight
    else:
        return (cnt - min_cnt) / (max_cnt - min_cnt) * common.figheight

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

print "  %% Number of store CFGs"
print "  \\draw[->] (0,0) -- (0,%f); " % common.figheight
for t in xrange(0,21,2):
    print "  \\node at (0, %f) [left] {%s};" % (count_to_y(float(t)), t)
    print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (count_to_y(float(t)), common.figwidth, count_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {Number of interfering \\glspl{cfg}};" % (common.figheight / 2)
for (alpha, data) in series.iteritems():
    samples = [x["nr_store_cfgs"] for x in data if x["gsc_timed_out"] == False]
    mean = common.mean(samples)
    common.draw_box_plot(common.alpha_to_x(alpha), count_to_y, samples, mean)

offset = common.figheight + figsep

print "  %% Time to build store CFGs"
print "  \\draw[->] (0,%f) -- (0,%f);" % (offset, offset + common.figheight)
for t in ["0.0001", "0.001", "0.01", "0.1", "1", "10", "60"]:
    print "  \\node at (0,%f) [left] {%s};" % (offset + time_to_y(float(t)), t)
    print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (offset + time_to_y(float(t)), common.figwidth, offset + time_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {Time taken deriving \\glspl{cfg}, seconds};" % (offset + common.figheight / 2)
for (alpha, data) in series.iteritems():
    samples = [x["gsc_time"] for x in data if x["gsc_timed_out"] == False]
    nr_timeouts = len([x for x in data if x["gsc_timed_out"] == True])
    mean = common.mean(samples)

    samples += [max_time] * nr_timeouts
    print
    print "  %%%% alpha = %d" % alpha
    common.draw_box_plot(common.alpha_to_x(alpha), lambda t: offset + time_to_y(t), samples, mean)

offset += common.figheight + figsep

# Now do the timeout rate
bpm_data = []
gsc_data = []
for (alpha, data) in series.iteritems():
    bpm_timeouts = len([x for x in data if x["bpm_time"] == None])
    gsc_timeouts = len([x for x in data if x["gsc_timed_out"] == True])
    no_timeout = len([x for x in data if x["gsc_timed_out"] == False])
    tot = float(no_timeout + gsc_timeouts + bpm_timeouts)
    bpm_data.append((alpha, bpm_timeouts / tot))
    gsc_data.append((alpha, (gsc_timeouts + bpm_timeouts) / tot))
    sys.stderr.write("Alpha = %d, %d bpm timeouts, %d gsc timeouts, %d non timeout, rates %f, %f\n" % (alpha, bpm_timeouts,
                                                                                                       gsc_timeouts, no_timeout,
                                                                                                       bpm_timeouts / tot,
                                                                                                       (bpm_timeouts + gsc_timeouts) / tot))
common.timeout_chart(offset, timeoutheight, 1.0, {"": bpm_data, " ": gsc_data}, 20)
if len(sys.argv) > 1 and sys.argv[1] == "opt":
    delta1 = "below "
    delta2 = "above "
else:
    delta1 = ""
    delta2 = ""
print "  \\node at (%f,%f) [%sright] {\\shortstack[l]{Building crashing\\\\thread only}};" % (common.figwidth, offset + timeoutheight * bpm_data[-1][1],delta1)
print "  \\node at (%f,%f) [%sright] {Building both threads};" % (common.figwidth, offset + timeoutheight * gsc_data[-1][1],delta2)
common.box_legend(0, False)

print "\\end{tikzpicture}"
