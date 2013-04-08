#! /usr/bin/env python

import os
import sys
import math

import common

common.figheight = 7.0
timeoutheight = 3

figsep = 1

min_count = 0.0
max_count = 1000.0
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
for (alpha, data) in series.iteritems():
    d = []
    for sample in data:
        i = sample["interferers"]
        if i != None:
            d += i
    s[alpha] = d
series = s

common.preamble()
common.alpha_axis(series)

offset = 0

s = series.items()
s.sort()

print "  %% Number of VCs generated"
print "  \\draw[->] (0,%f) -- (0,%f);" % (offset, offset + common.figheight)
for t in xrange(0,max_count+1,200):
    print "  \\node at (0, %f) [left] {%s};" % (offset + count_to_y(float(t)), t)
    print "  \\draw [color=black!10] (0,%f) -- (%f, %f);" % (offset + count_to_y(float(t)), common.figwidth, offset + count_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {\\shortstack{Total number of\\\\\\glspl{verificationcondition}\\\\(solid)}};" % (offset + common.figheight / 2)
print "  \\draw (0, %f)" % (offset)
for (alpha, data) in s:
    samples = [x["generated_vc"] for x in data if x["generated_vc"] != False]
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), count_to_y(len([x for x in samples if x == True])) + offset)
print "        ;"

print "  %% Proportion generating VCs"
print "  \\draw[->] (%f,%f) -- (%f,%f);" % (common.figwidth, offset, common.figwidth, offset + common.figheight)
for t in xrange(0,101,20):
    print "  \\node at (%f, %f) [right] {%d\\%%};" % (common.figwidth, prop_to_y(t/100.0), t)
print "  \\node at (%f, %f) [rotate=-90, anchor=south] {\\shortstack{Proportion generating \\\\\\glspl{verificationcondition}\\\\(dashed)}};" % (common.figwidth + .8, offset + common.figheight / 2)
print "  \\draw[dashed] (0, %f)" % (offset)
for (alpha, data) in s:
    samples = [x["generated_vc"] for x in data if x["generated_vc"] != None]
    print "        -- (%f, %f)" % (common.alpha_to_x(alpha), prop_to_y(len([x for x in samples if x == True]) / float(len(samples))) + offset)
print "        ;"

offset = common.figheight + figsep

print "  %% Time to generate VCs"
print "  \\draw[->] (0,%f) -- (0,%f);" % (offset, offset + common.figheight)
for t in ["0.001", "0.01", "0.1", "1", "10", "60"]:
    print "  \\node at (0,%f) [left] {%s};" % (offset + time_to_y(float(t)), t)
    print "  \\draw [color=black!10] (0,%f) -- (%f, %f);" % (offset + time_to_y(float(t)), common.figwidth, offset + time_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {\\shortstack{Time to derive \\glspl{verificationcondition}\\\\(seconds)}};" % (offset + common.figheight / 2)
for (alpha, data) in series.iteritems():
    samples = [x["gvc_time"] for x in data if x["gvc_timeout"] == False]
    nr_timeouts = len([x for x in data if x["gvc_timeout"] != False])
    mean = common.mean(samples)

    samples += [max_time] * nr_timeouts
    print
    print "  %%%% alpha = %d" % alpha
    print "  %%%% samples = %s" % str(samples)
    print "  %%%% nr_timeout = %d" % nr_timeouts
    common.draw_box_plot(common.alpha_to_x(alpha), lambda t: offset + time_to_y(t), samples, mean)
common.box_legend(offset)

offset += common.figheight + figsep

timeout_data = []
for (alpha, data) in series.iteritems():
    timeouts = len([x for x in data if x["bsm_time"] == None or x["gvc_timeout"] == True])
    timeout_data.append((alpha, timeouts / float(len(data))))
common.timeout_chart(offset, timeoutheight, 1.0, {"": timeout_data}, 20)

print "\\end{tikzpicture}"
