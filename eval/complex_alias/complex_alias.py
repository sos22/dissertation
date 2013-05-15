#! /usr/bin/env python

import sys
import math
import re
import os
import itertools

figwidth = 7.0
figheight = 7.0
sep = 1.0
tick_width = 0.05
timeout_time = 300
oom_mem = 2353004544

step = 5

def float_range(start, end, nr_levels):
    i = float(start)
    step = (end - i) / nr_levels
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
    nr_loads = int(w[0]) / step
    nr_stores = int(w[1]) / step
    k = (nr_loads, nr_stores)
    if not times.has_key(k):
        assert not mems.has_key(k)
        times[k] = []
        mems[k] = []
    if w[2] in ["OOM", "timeout"]:
        if w[2] == "OOM":
            ooms[k] = ooms.get(k, 0) + 1
        else:
            timeouts[k] = timeouts.get(k, 0) + 1
        mems[k].append(oom_mem * 2)
        times[k].append(timeout_time * 2)
    else:
        times[k].append(float(w[3]))
        mems[k].append(long(w[2]))

def rr(lower, upper, contours):
    if upper < lower:
        (lower, upper) = (upper, lower)
    for c in contours:
        if lower <= c < upper:
            yield c

def mean(data):
    return sum(data) / len(data)
def contour_map(extent, data, suppress, nr_contours, timeouts, ooms,
                contours, contour_labels):
    def all_keys():
        return itertools.chain((x for x in data),
                               (x for x in timeouts.iterkeys()),
                               (x for x in ooms.iterkeys()))
    min_x = min(itertools.imap(lambda x: x[0], all_keys()))
    min_y = min(itertools.imap(lambda x: x[1], all_keys()))
    max_x = max(itertools.imap(lambda x: x[0], all_keys()))
    max_y = max(itertools.imap(lambda x: x[1], all_keys()))
    def scale_x(x):
        return (x - min_x) / float(max_x - min_x) * (extent[1][0] - extent[0][0]) + extent[0][0]
    def scale_y(y):
        return (y - min_y) / float(max_y - min_y) * (extent[1][1] - extent[0][1]) + extent[0][1]

    print "  %%% Contour map"
    print "  %% X marks"
    for x in xrange(min_x, max_x, 5):
        print "  \\node at (%f,%f) [below] {%d};" % (scale_x(x), scale_y(min_y), x * step)
        print "  \\draw [color=black!10] (%f, %f) -- (%f, %f);" % (scale_x(x), scale_y(min_y),
                                                                   scale_x(x), scale_y(max_y))
    print "  \\node at (%f,%f) [below] {Number of loads};" % ((scale_x(min_x) + scale_x(max_x)) / 2,
                                                              scale_y(min_y) - .42)

    print "  %% Y marks"
    for y in xrange(min_y, max_y, 5):
        print "  \\node at (%f,%f) [left] {%d};" % (scale_x(min_x), scale_y(y), y * step)
        print "  \\draw [color=black!10] (%f, %f) -- (%f, %f);" % (scale_x(min_x), scale_y(y),
                                                                   scale_x(max_x), scale_y(y))
    print "  \\node at (%f,%f) [rotate=90, below] {Number of stores};" % (scale_x(min_x) - 1.2,
                                                                          (scale_y(min_y) + scale_y(max_y)) / 2)

    for (x,y) in data.iterkeys():
        if timeouts.has_key((x, y)) or ooms.has_key((x, y)):
            continue
        (x0, y0) = (scale_x(x), scale_y(y))
        print "  \\fill [color=black!20] (%f, %f) rectangle (%f,%f);" % (x0-0.01, y0-0.01,
                                                                         x0+0.01, y0+0.01)
    print "  %% Axes"
    print "  \\draw (%f,%f) -- (%f,%f);" % (scale_x(min_x), scale_y(min_y),
                                            scale_x(min_x), scale_y(max_y))
    print "  \\draw (%f,%f) -- (%f,%f);" % (scale_x(min_x), scale_y(min_y),
                                            scale_x(max_x), scale_y(min_y))

    label_posns = {} # Map from contour to (x, y, bearing) of best
                     # place to put that countour which we've found so
                     # far.

    for x in xrange(min_x, max_x):
        for y in xrange(min_y, max_y):
            s = suppress(x, y)
            if s != None:
                print "  \\path [fill,%s] (%f, %f) rectangle (%f,%f);" % (s,
                                                                          scale_x(x),
                                                                          scale_y(y),
                                                                          scale_x(x+1),
                                                                          scale_y(y+1))
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
                return (x2, scale_y(y + 1), "top")
            def bottom(contour):
                if br == bl:
                    x2 = scale_x(x + .5)
                else:
                    x2 = scale_x(x + (contour - bl) / (br - bl))
                return (x2, scale_y(y), "bottom")
            def left(contour):
                if tl == bl:
                    y2 = scale_y(y + .5)
                else:
                    y2 = scale_y(y + (contour - bl) / (tl - bl))
                return (scale_x(x), y2, "left")
            def right(contour):
                if tr == br:
                    y2 = scale_y(y + .5)
                else:
                    y2 = scale_y(y + (contour - br) / (tr - br))
                return (scale_x(x + 1), y2, "right")
            def ln(t, a, b):
                print "  \\draw [color=black!75] (%f, %f) -- (%f, %f); %% %f; %s -> %s" % (a[0], a[1],
                                                                                           b[0], b[1],
                                                                                           t,
                                                                                           a[2], b[2])
                if b[2] == "right":
                    usedr.append(t)
                elif b[2] == "bottom":
                    usedb.append(t)
                elif b[2] == "left":
                    usedl.append(t)
                else:
                    abort()
                if t in contour_labels:
                    # Distance is square distance from point to the
                    # diagonal, and we try to get as close as
                    # possible.
                    def defect(x, y):
                        return x ** 2 + y ** 2 - (x + y) ** 2 / 2
                    (x,y) = ((a[0] + b[0])/2, (a[1] + b[1])/2)
                    newDist = defect(x, y)
                    if not label_posns.has_key(t):
                        # Hack: all that matters is that it's bigger than newDist
                        oldDist = newDist + 1
                    else:
                        oldLabel = label_posns[t]
                        oldDist = defect(oldLabel[0], oldLabel[1])
                    if newDist < oldDist:
                        bearing = math.atan2(a[1] - b[1], a[0] - b[0])
                        label_posns[t] = (x, y, bearing)
            usedr = []
            usedb = []
            usedl = []
            # Things coming in the top
            for t in rr(tl, tr, contours):
                # Figure out where we're going
                if br <= t < tr or tr <= t < br:
                    ln(t, top(t), right(t))
                elif bl <= t < br or br <= t < bl:
                    ln(t, top(t), bottom(t))
                else:
                    ln(t, top(t), left(t))
            # Things coming in on the right
            for t in rr(tr, br, contours):
                if t in usedr:
                    continue
                if bl <= t < br or br <= t < bl:
                    ln(t, right(t), bottom(t))
                else:
                    ln(t, right(t), left(t))
            # Things coming in the bottom
            for t in rr(bl, br, contours):
                if t in usedb:
                    continue
                # Have to go out the left
                assert bl <= t <= br or br <= t <= bl
                ln(t, bottom(t), left(t))
            # Things coming in the left.  Should have already been handled
            for t in rr(bl, tl, contours):
                assert t in usedl
    # Defect marks
    for ((x,y), nr_timeouts) in timeouts.iteritems():
        (x0, y0) = (scale_x(x), scale_y(y))
        print "  \\draw (%f, %f) -- (%f, %f);" % (x0-0.05,y0-0.05,
                                                  x0+0.05,y0+0.05)
        print "  \\draw (%f, %f) -- (%f, %f);" % (x0-0.05,y0+0.05,
                                                  x0+0.05,y0-0.05)
    for ((x, y), nr_timeouts) in ooms.iteritems():
        (x0, y0) = (scale_x(x), scale_y(y))
        print "  \\draw (%f, %f) circle(.7mm);" % (x0, y0)

    # Line labels
    for (k, (x, y, bearing)) in label_posns.iteritems():
        b = bearing * 360 / (2 * math.pi)
        if b > 90 and b < 180:
            b -= 180
        print "  \\node at (%f, %f) [rotate=%f] {\small %d};" % (x, y, b, k)
        sys.stderr.write("Bearing for %d -> %f\n" % (k, b))

print "\\begin{tikzpicture}"

failed = ooms.copy()
for (k, v) in timeouts.iteritems():
    failed[k] = failed.get(k, 0) + v
def suppress(x, y):
    if (x,y) in failed or (x+1,y) in failed or (x,y+1) in failed or (x+1,y+1) in failed:
        return "color=red"
    else:
        return None
contour_map( ((0,0),(figwidth,figheight)), times, suppress, 10, timeouts, ooms,
             [1.0/(10**.5), 1.0, 10**.5, 10.0, 10 * 10**.5, 100.0, 100 * 10**.5],
             set([1.0, 10.0, 100.0]) )
contour_map( ((figwidth+sep, 0), (figwidth * 2 + sep, figheight)), mems, suppress, 10, timeouts, ooms,
             [ 1e6, 5e6, 10e6, 50e6, 100e6, 500e6, 1000e6, 2000e6],
             set())

print "\\end{tikzpicture}"
