#! /usr/bin/env python

import common
import math

common.figheight = 7
common.figwidth /= 3
common.box_width /= 3
max_cnt = 20000.0
min_cnt = 1.0

def count_to_y(cnt):
    if cnt <= min_cnt:
        return 0
    elif cnt > max_cnt:
        return common.figheight
    else:
        return math.log(cnt / min_cnt) / math.log(max_cnt / min_cnt) * common.figheight

def alpha_axis(offset, series, foo, description):
    s = series.keys()
    s.sort()
    print "  \\draw[->] (%f,0) -- (%f,0);" % (offset + common.alpha_to_x(s[0]),
                                              offset + common.alpha_to_x(s[-1]))
    for i in xrange(len(s)):
        if i % 2 == foo:
            print "  \\node at (%f,0) [below] {%d};" % (offset + common.alpha_to_x(s[i]), s[i])
        else:
            print "  \\node at (%f,-12pt) [below] {%d};" % (offset + common.alpha_to_x(s[i]), s[i])
    print "  \\node at (%f, %f) [above] {%s};" % (offset + common.figwidth / 2,
                                                  common.figheight,
                                                  description)
series = common.read_input()
common.preamble()

print "  %% Y axis"
print "  \\draw[->] (0,0) -- (0,%f); " % common.figheight
for t in ["1", "10", "100", "1000", "10000", "20000"]:
    print "  \\node at (0, %f) [left] {%s};" % (count_to_y(float(t)), t)
    print "  \\draw [color=black!10] (0, %f) -- (%f, %f);" % (count_to_y(float(t)), common.figwidth * 3, count_to_y(float(t)))
print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {Count};" % (common.figheight / 2)

def do_one(offset, alpha, key, data):
    samples = [x[key] for x in data if x[key] != None]
    if len(samples) == 0:
        return
    mean = common.mean(samples)
    common.draw_box_plot(common.alpha_to_x(alpha) + offset, count_to_y, samples, mean)
keys = ["nr_crashing_instrs", "initial_crashing_states", "simplified_crashing_states"]
descrs = ["Instructions", "Unsimplified states", "Simplified states"]
for k in xrange(len(keys)):
    print "  %%%% k = %s" % keys[k]
    alpha_axis(common.figwidth * k, series, k % 2, descrs[k])
    for (alpha, (data, _)) in series.iteritems():
        do_one(k * common.figwidth, alpha, keys[k], data)

common.figwidth *= 3
print "  \\node at (%f, -24pt) [below] {Value of \\gls{alpha}};" % (common.figwidth / 2)
common.box_legend(0)

print "\\end{tikzpicture}"
