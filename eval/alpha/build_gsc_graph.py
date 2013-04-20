#! /usr/bin/env python

import os
import sys
import math
import common

common.figheight = 7.0
timeoutheight = 3
figsep = 1
common.height_pre_dismiss_box = 2.5
common.mintime = 0.001
max_cnt = 40.0
min_cnt = 0.0

def count_to_y(cnt):
    if cnt <= min_cnt:
        return 0
    elif cnt > max_cnt:
        return common.figheight
    else:
        return (cnt - min_cnt) / (max_cnt - min_cnt) * common.figheight

series = common.read_input()
common.preamble()
common.alpha_axis(series)

print "  %% Number of store CFGs"
print "  \\draw[->] (0,0) -- (0,%f); " % common.figheight
for t in xrange(0,41,5):
    print "  \\node at (0, %f) [left] {%s};" % (count_to_y(float(t)), t)
    print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (count_to_y(float(t)), common.figwidth, count_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {Number of interfering \\glspl{cfg}};" % (common.figheight / 2)
for (alpha, (data, _)) in series.iteritems():
    samples = [x["nr_store_cfgs"] for x in data if x["early-out"] == False and x["bpm_timeout"] == False and x["bpm_oom"] == False and x["skip_gsc"] == False and x["gsc_timed_out"] == False and x["gsc_oom"] == False]
    mean = common.mean(samples)
    common.draw_box_plot(common.alpha_to_x(alpha), count_to_y, samples, mean)
common.box_legend(0, True)

offset = common.figheight + figsep

common.box_width = 2.0
common.figheight = 12.0

common.kde_axis(offset, True, True, True, True)

def parse_series(data):
    if data == None:
        return None
    nr_dismiss = 0
    nr_pre_failed = 0
    nr_timeouts = 0
    nr_oom = 0
    samples = []
    for x in data:
        if x["early-out"] == True:
            nr_dismiss += 1
            continue
        if x["bpm_timeout"] or x["bpm_oom"]:
            nr_pre_failed += 1
            continue
        if x["skip_gsc"] == True:
            nr_dismiss += 1
            continue
        if x["gsc_timed_out"]:
            nr_timeouts += 1
            continue
        if x["gsc_oom"]:
            nr_oom += 1
            continue
        samples.append(x["gsc_time"])
    return {"times": samples, "nr_post_timeout": nr_timeouts,
            "nr_pre_dismiss": nr_dismiss, "nr_post_oom": nr_oom,
            "nr_pre_failure": nr_pre_failed}
for (alpha, data) in series.iteritems():
    with_repeats = parse_series(data[0])
    without_repeats = parse_series(data[1])
    print
    print "  %%%% alpha = %d" % alpha
    common.kde_chart(offset, common.alpha_to_x(alpha), with_repeats, without_repeats)

print "\\end{tikzpicture}"
