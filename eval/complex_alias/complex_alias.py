#! /usr/bin/env python

import sys
import math
import re
import os

figwidth = 6.0
figheight = 20.0
sep = 1.0
tick_width = 0.05

max_loads = 0
max_stores = 0
max_time = 120.0

def float_range(start, end, step):
    i = float(start)
    while i < end:
        yield i
        i += step
def draw_tick(x, y, decoration = ""):
    print "  \\draw %s (%f, %f) -- (%f, %f);" % (decoration,
                                                 x - tick_width, y - tick_width,
                                                 x + tick_width, y + tick_width)
    print "  \\draw %s (%f, %f) -- (%f, %f);" % (decoration,
                                                 x + tick_width, y - tick_width,
                                                 x - tick_width, y + tick_width)

# Slurp in the data
times = {}
mems = {}
ooms = {}
timeouts = {}
for l in sys.stdin.xreadlines():
    w = l.strip().split()
    nr_loads = int(w[0])
    nr_stores = int(w[1])
    k = (nr_loads, nr_stores)
    if w[2] == "OOM":
        ooms[k] = ooms.get(k) + 1
        continue
    if w[2] == "timeout":
        timeouts[k] = timeouts.get(k) + 1
        continue
    if not times.has_key(k):
        assert not mems.has_key(k)
        times[k] = []
        mems[k] = []
    times[k].append(float(w[3]))
    mems[k].append(long(w[2]))

for oom in ooms:
    if times.has_key(oom):
        del times[oom]
        del mems[oom]
for timeout in timeouts:
    if times.has_key(timeout):
        del times[timeout]
        del mems[timeout]

def rr(lower, upper, contours):
    if upper < lower:
        (lower, upper) = (upper, lower)
    for c in contours:
        if lower <= c < upper:
            yield c

def mean(data):
    return sum(data) / len(data)
def contour_map(extent, data, suppress, nr_contours):
    min_x = min([x[0] for x in data])
    min_y = min([x[1] for x in data])
    max_x = max([x[0] for x in data])
    max_y = max([x[1] for x in data])
    def scale_x(x):
        return (x - min_x) / float(max_x - min_x) * (extent[1][0] - extent[0][0]) + extent[0][0]
    def scale_y(y):
        return (y - min_y) / float(max_y - min_y) * (extent[1][1] - extent[0][1]) + extent[0][1]

    print "  %%% Contour map"
    print "  %% X axis"
    print "  \\draw (%f,%f) -- (%f,%f);" % (scale_x(min_x), scale_y(min_y),
                                            scale_x(max_x), scale_y(min_y))
    for x in xrange(min_x, max_x):
        print "  \\node at (%f,%f) [below] {%d};" % (scale_x(x), scale_y(min_y), x)
        print "  \\draw [color=black!10] (%f, %f) -- (%f, %f);" % (scale_x(x), scale_y(min_y),
                                                                   scale_x(x), scale_y(max_y))
    print "  %% Y axis"
    print "  \\draw (%f,%f) -- (%f,%f);" % (scale_x(min_x), scale_y(min_y),
                                            scale_x(min_x), scale_y(max_y))
    for y in xrange(min_y, max_y):
        print "  \\node at (%f,%f) [left] {%d};" % (scale_x(min_x), scale_y(y), y)
        print "  \\draw [color=black!10] (%f, %f) -- (%f, %f);" % (scale_x(min_x), scale_y(y),
                                                                   scale_x(max_x), scale_y(y))

    min_data = min([min(x) for x in data.itervalues()])
    max_data = max([max(x) for x in data.itervalues()])

    contours = list(float_range(min_data, max_data, (max_data - min_data) / nr_contours))
    print "  %% contours = %s" % str(contours)
    for x in xrange(min_x, max_x):
        for y in xrange(min_y, max_y):
            s = suppress(x, y)
            if s != None:
                print "  \\path [fill,%s] (%f, %f) rectangle (%f,%f);" % (s,
                                                                          scale_x(x),
                                                                          scale_y(y),
                                                                          scale_x(x+1),
                                                                          scale_y(y+1))
                continue
            bl = data.get((x, y), None)
            tl = data.get((x, y+1), None)
            br = data.get((x+1, y), None)
            tr = data.get((x+1, y+1), None)
            if bl == None or tl == None or br == None or tr == None:
                continue
            bl = mean(bl)
            tl = mean(tl)
            br = mean(br)
            tr = mean(tr)
            print "  %%%% Cell coords (%d,%d), corners tl = %f, tr = %f, br = %f, bl = %f" % (x, y,
                                                                                              tl, tr, br, bl)
            def top(contour):
                if tr == tl:
                    x2 = scale_x(x + .5)
                else:
                    x2 = scale_x(x + (contour - tl) / (tr - tl))
                return "(%f, %f)" % (x2, scale_y(y + 1))
            def bottom(contour):
                if br == bl:
                    x2 = scale_x(x + .5)
                else:
                    x2 = scale_x(x + (contour - bl) / (br - bl))
                return "(%f, %f)" % (x2, scale_y(y))
            def left(contour):
                if tl == bl:
                    y2 = scale_y(y + .5)
                else:
                    y2 = scale_y(y + (contour - bl) / (tl - bl))
                return "(%f, %f)" % (scale_x(x), y2)
            def right(contour):
                if tr == br:
                    y2 = scale_y(y + .5)
                else:
                    y2 = scale_y(y + (contour - br) / (tr - br))
                return "(%f, %f)" % (scale_x(x + 1), y2)
            usedr = []
            usedb = []
            usedl = []
            # Things coming in the top
            for t in rr(tl, tr, contours):
                print "  \\draw %s -- " % top(t),
                # Figure out where we're going
                if br <= t < tr or tr <= t < br:
                    print "%s; %% %f, top -> right" % (right(t), t)
                    usedr.append(t)
                elif bl <= t < br or br <= t < bl:
                    print "%s; %% %f, top -> bottom" % (bottom(t), t)
                    usedb.append(t)
                else:
                    print "%s; %% %f, top -> left" % (left(t), t)
                    usedl.append(t)
            # Things coming in on the right
            for t in rr(tr, br, contours):
                if t in usedr:
                    continue
                print "  \\draw %s -- " % right(t),
                if bl <= t < br or br <= t < bl:
                    print "%s; %% %f, right -> bottom " % (bottom(t), t)
                    usedb.append(t)
                else:
                    print "%s; %% %f, right -> left" % (left(t), t)
                    usedl.append(t)
            # Things coming in the bottom
            for t in rr(bl, br, contours):
                if t in usedb:
                    continue
                # Have to go out the left
                assert bl <= t <= br or br <= t <= bl
                print "  \\draw %s -- %s; %% %f, bottom -> left" % (bottom(t), left(t), t)
                usedl.append(t)
            # Things coming in the left.  Should have already been handled
            for t in rr(bl, tl, contours):
                assert t in usedl

print "\\begin{tikzpicture}"

failed = ooms.copy()
for (k, v) in timeouts.iteritems():
    failed[k] = failed.key(k, 0) + v
def suppress(x, y):
    if (x,y) in failed or (x+1,y) in failed or (x,y+1) in failed or (x+1,y+1) in failed:
        return "color=red"
    else:
        return None
contour_map( ((0,0),(figwidth,figheight)), times, suppress, 10)
contour_map( ((figwidth+sep, 0), (figwidth * 2 + sep, figheight)), mems, suppress, 10)

print "\\end{tikzpicture}"
