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
    samples = [x["nr_store_cfgs"] for x in data if x["early-out"] == False and x["skip_gsc"] == False and x["gsc_timed_out"] == False]
    mean = common.mean(samples)
    common.draw_box_plot(common.alpha_to_x(alpha), count_to_y, samples, mean)
common.box_legend(0, True)

offset = common.figheight + figsep

common.kde_axis(offset, True, True, True, True)

for limm in [False, True]:
    for (alpha, data) in series.iteritems():
        nr_dismiss = 0
        nr_pre_failed = 0
        nr_timeouts = 0
        samples = []
        for x in data:
            if x["early-out"] == True or x["skip_gsc"] == True:
                nr_dismiss += 1
                continue
            if x["bpm_time"] == None:
                nr_pre_failed += 1
                continue
            if x["gsc_timed_out"]:
                nr_timeouts += 1
                continue
            samples.append(x["gsc_time"])
        print
        print "  %%%% alpha = %d" % alpha
        common.kde_chart(offset, common.alpha_to_x(alpha), nr_dismiss, nr_pre_failed, samples, nr_timeouts, 0, limm)

print "\\end{tikzpicture}"
