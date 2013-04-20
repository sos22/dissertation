#! /usr/bin/env python

import math
import common

timeoutheight = 3.0
common.figheight = 7.0
common.box_width = 0.5
common.mintime = 0.001

series = common.read_input()
common.preamble()
common.alpha_axis(series)

common.kde_axis(0, True, False, True, True)

# Now plot the series
def parse_series(data):
    if data == None:
        return None
    times = []
    nr_timeouts = 0
    nr_early_out = 0
    nr_oom = 0
    for x in data:
        if x["early-out"]:
            nr_early_out += 1
            continue
        if x["bpm_oom"]:
            nr_oom += 1
            continue
        if x["bpm_timeout"]:
            nr_timeouts+=1
            continue
        assert x["bpm_time"] != None
        times.append(x["bpm_time"])
    return {"times": times, "nr_post_timeout": nr_timeouts,
            "nr_pre_dismiss": nr_early_out, "nr_post_oom": nr_oom,
            "nr_pre_failure": None}
for (alpha, data) in series.iteritems():
    with_repeats = parse_series(data[0])
    without_repeats = parse_series(data[1])
    print
    print "  %%%% alpha = %d" % alpha
    common.kde_chart(0, common.alpha_to_x(alpha), with_repeats, without_repeats)

print "\\end{tikzpicture}"
