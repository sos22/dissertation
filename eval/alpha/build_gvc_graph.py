#! /usr/bin/env python

import os
import sys
import math

import common

common.mintime = 0.0001
common.figheight = 7.0
timeoutheight = 3

figsep = 1

min_count = 0.0
max_count = 2000.0
min_time = 0.0001
max_time = 60

def count_to_y(cnt):
    return (cnt - min_count) / (max_count - min_count) * common.figheight
def prop_to_y(cnt):
    return cnt * common.figheight
def time_to_y(time):
    if time < min_time:
        return 0
    elif time > max_time:
        return common.figheight
    else:
        return math.log(time / min_time) / math.log(max_time / min_time) * common.figheight

series = common.read_input()

s = {}
for (alpha, (data0, data1)) in series.iteritems():
    d0 = []
    for sample in data0:
        if not "interferers" in sample:
            continue
        i = sample["interferers"]
        if i != None:
            d0 += i.values()
    if data1 == None:
        d1 = None
    else:
        d1 = []
        for sample in data1:
            if not "interferers" in sample:
                continue
            i = sample["interferers"]
            if i != None:
                d1 += i.values()
    s[alpha] = (d0, d1)
series = s

common.preamble()
common.alpha_axis(series)

offset = 0

s = series.items()
s.sort()

print "  %% Number of VCs generated"
print "  \\draw[->] (0,%f) -- (0,%f);" % (offset, offset + common.figheight)
for t in xrange(0,max_count+1,400):
    print "  \\node at (0, %f) [left] {%s};" % (offset + count_to_y(float(t)), t)
    print "  \\draw [color=black!10] (0,%f) -- (%f, %f);" % (offset + count_to_y(float(t)), common.figwidth, offset + count_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {\\shortstack{Total number of\\\\\\glspl{verificationcondition}\\\\(solid)}};" % (offset + common.figheight / 2)
print "  \\draw (0, %f)" % (offset)
for (alpha, (data, _)) in s:
    samples = [x["generated_vc"] for x in data if not x["gvc_timeout"] and x["generated_vc"] != None]
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), count_to_y(len([x for x in samples if x == True])) + offset)
print "        ;"

print "  %% Proportion generating VCs"
print "  \\draw[->] (%f,%f) -- (%f,%f);" % (common.figwidth, offset, common.figwidth, offset + common.figheight)
for t in xrange(0,101,20):
    print "  \\node at (%f, %f) [right] {%d\\%%};" % (common.figwidth, prop_to_y(t/100.0), t)
print "  \\node at (%f, %f) [rotate=-90, anchor=south] {\\shortstack{Proportion generating \\\\\\glspl{verificationcondition}\\\\(dashed)}};" % (common.figwidth + .8, offset + common.figheight / 2)
print "  \\draw[dashed] (0, %f)" % (offset)
for (alpha, (data, _)) in s:
    samples = [x["generated_vc"] for x in data if not x["gvc_timeout"] and x["generated_vc"] != None]
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), prop_to_y(len([x for x in samples if x == True]) / float(len(samples))) + offset)
print "        ;"

offset = common.figheight + figsep

def parse_series(data):
    if data == None:
        return None
    samples = []
    nr_timeouts = 0
    nr_oom = 0
    for x in data:
        if x["gvc_timeout"]:
            nr_timeouts += 1
            continue
        if x["gvc_oom"]:
            nr_oom += 1
            continue
        samples.append(x["gvc_time"])
    return {"times": samples, "nr_post_timeout": nr_timeouts,
            "nr_pre_dismiss": None, "nr_post_oom": nr_oom,
            "nr_pre_failure": None}
common.kde_axis(offset, False, False, True, True)
for (alpha, data) in series.iteritems():
    print
    print "  %%%% alpha = %d" % alpha
    common.kde_chart(offset, common.alpha_to_x(alpha), parse_series, data)

print "\\end{tikzpicture}"
