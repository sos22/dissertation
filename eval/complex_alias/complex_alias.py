#! /usr/bin/env python

import sys
import math
import re
import os
import itertools
import random

figwidth = 7.0
figheight = 7.0
sep = 1.0
tick_width = 0.05
timeout_time = 300
oom_mem = 2353004544
nr_replicates = 1000
confidence_size = 0.99
confidence_sd = 5

random.seed(0)

step = 5

def quantile(vals, q):
    q *= len(vals)
    idx0 = int(q)
    idx1 = idx0 + 1
    if idx1 >= len(vals):
        return vals[-1]
    return vals[idx0] * (1 - (q - idx0)) + vals[idx1] * (q - idx0)

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
    if w[0] == "Rep":
        continue
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

for v in times.itervalues():
    v.sort()
for v in mems.itervalues():
    v.sort()

def rr(lower, upper, contours):
    if upper < lower:
        (lower, upper) = (upper, lower)
    for c in contours:
        if lower <= c < upper:
            yield c

def mean_sd(data):
    mean = sum(data) / len(data)
    return (mean, (sum([(x - mean) ** 2 for x in data]) / (len(data) * (len(data) - 1))) ** .5)

# Assume that Y is a linear function of X.  We know that at X=0,
# Y ~ N(m0, s0) and at X=1 Y ~ N(m1, s1).  Try to find a confidence
# interval for the value of X which puts Y = val.
def intercept_confidence_interval(m0, s0, m1, s1, val, confidence):
    val = float(val) # For sanity

    if abs(m1 - m0) <= 0.01 * ((s0 ** 2 + s1 ** 2) ** .5):
        return None
    def intercept(y0, y1):
        return (val - y0) / (y1 - y0)
    # Fuck it, this is too hard to do analytically.  Bootstrap it.
    def gen_replicate():
        y0 = random.gauss(m0, s0)
        y1 = random.gauss(m1, s1)
        r = intercept(y0, y1)
        return r
    replicates = [gen_replicate() for _ in xrange(nr_replicates)]
    replicates.sort()
    r = (quantile(replicates, (1 - confidence) / 2),
         quantile(replicates, .5),
         quantile(replicates, (1 + confidence) / 2))
    assert (r[0] <= r[1] <= r[2]) or (r[2] <= r[1] <= r[0])
    return r

def defect(where):
    return min(((where[0] - ref[0]) ** 2 + (where[1] - ref[1]) ** 2) for ref in [(0,0),(0,1),(1,0),(1,1)])
# Try to massage things a bit so that it fits into a
# valid sequence.
def build_massaged(end_state, c_cntr, state, old, idx, memo):
    if idx == len(old):
        if state == end_state and (c_cntr % 2 == 0):
            return (0, [])
        else:
            return (1000, [])
    mem = memo.get((idx,state), None)
    if mem != None:
        return mem
    e = old[idx]
    key = e[0]
    where = e[1]
    if key == "V":
        # Always take these.
        (a, b) = build_massaged(end_state, c_cntr, state, old, idx + 1, memo)
        return (a, [e] + b)

    if key == "*" and state != 0:
        if 0 <= where[0] <= 1 and 0 <= where[1] <= 1:
            if state == -1:
                (a, b) = build_massaged(end_state, c_cntr + 1, 1, old, idx + 1, memo)
                return (a, [("L+", where), ("C", where), ("U+", where)] + b)
            else:
                (a, b) = build_massaged(end_state, c_cntr + 1, -1, old, idx + 1, memo)
                return (a, [("U-", where), ("C", where), ("L-", where)] + b)
        else:
            return build_massaged(end_state, c_cntr, state, old, idx + 1, memo)
    # Is it valid to take this one?
    isValid = ((state == 0 and key in ["L-", "C", "U+"]) or (state == -1 and key == "L+") or (state == 1 and key == "U-"))
    if key == "C" and isValid:
        # Have to take it.
        (take_defect, take_rest) = build_massaged(end_state, c_cntr + 1, state, old, idx + 1, memo)
        res = (take_defect, [e] + take_rest)
        memo[(idx, state)] = res
        return res

    (skip_defect, skip_rest) = build_massaged(end_state, c_cntr, state, old, idx + 1, memo)
    skip_defect += defect(where)
    if not isValid:
        # Have to skip it
        res = (skip_defect, skip_rest)
        memo[(idx, state)] = res
        return res
    assert key != "C"
    # Have a choice between skipping and taking.  Go with whichever
    # one minimises the total defect.
    next_state = state
    new_key = key
    if key == "L-":
        next_state = -1
    elif key == "U+":
        next_state = 1
    elif key in ["L+", "U-"]:
        next_state = 0
    (take_defect, take_rest) = build_massaged(end_state, c_cntr, next_state, old, idx + 1, memo)
    if take_defect < skip_defect:
        res = (take_defect, [(new_key, where)] + take_rest)
    else:
        res = (skip_defect, skip_rest)
    memo[(idx, state)] = res
    return res

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
    print "  \\node at (%f,%f) [below] {Number of loads};" % ((scale_x(min_x) + scale_x(max_x)) / 2,
                                                              scale_y(min_y) - .42)

    print "  %% Y marks"
    for y in xrange(min_y, max_y, 5):
        print "  \\node at (%f,%f) [left] {%d};" % (scale_x(min_x), scale_y(y), y * step)
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

    print "  %% xrange %f -> %f, yrange %f -> %f" % (min_x, max_x, min_y, max_y)
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
                print "  %%%% Cell coords (%d,%d) missing" % (x, y)
                continue
            (bl,bls) = mean_sd(bl)
            (tl,tls) = mean_sd(tl)
            (br,brs) = mean_sd(br)
            (tr,trs) = mean_sd(tr)
            print "  %%%% Cell coords (%d,%d), corners tl = %f, tr = %f, br = %f, bl = %f" % (x, y,
                                                                                              tl, tr, br, bl)

            # Which contours intersect this cell at all?
            lowest = min([bl - bls * confidence_sd,
                          tl - tls * confidence_sd,
                          br - brs * confidence_sd,
                          tr - trs * confidence_sd])
            highest = max([bl + bls * confidence_sd,
                           tl + tls * confidence_sd,
                           br + brs * confidence_sd,
                           tr + trs * confidence_sd])
            ccs = []
            for xc in contours:
                if lowest < xc < highest:
                    ccs.append(xc)
            ccs.sort()

            # We encode each confidence level for each cell into a
            # series of events which represent what can happen as you
            # walk around the edge of the cell.  The possible events
            # are:
            #
            # L+ -- entered the confidence interval by crossing the lower
            #       bound
            # L- -- left the confidence interval by crossing the lower
            #       bound
            # C -- reached the MLE estimate of the contour
            # U- -- entered the confidence interval by crossing the upper
            #       bound
            # U+ -- left the confidence interval by crossing the upper
            #       bound
            # V -- reached a corner of the cell (for vertex)
            #
            # This then feeds into a couple of state machines which
            # emit the actual contents of the cell.  The state
            # machines both have three states (below interval (-1), in
            # interval (0), above interval (+1)).  Events L-, C, and
            # U+ should only happen in state 0.  Event U- should only
            # happen in state 1.  Event L+ should only happen in state
            # -1.  The tricky part is that the intercepts are
            # themselves calculated by a bootstrap, and therefore have
            # some error, which leads to some interesting corner
            # cases.
            #
            # The event sequence starts in the top-left corner of the
            # cell and moves clockwise.
            #
            sm_inputs = {}
            for c in ccs:
                # Generate event sequence.
                events = []

                def do_line(pt, start_val, start_sd,
                            end_val, end_sd, reverse):
                    # Vertex
                    if reverse:
                        events.append(("V", pt(0))) 
                    else:
                        events.append(("V", pt(1))) 
                    # Contour intersections
                    alpha = intercept_confidence_interval(start_val, start_sd,
                                                          end_val, end_sd,
                                                          c, confidence_size)
                    print "  %% C = %f, start = %fpm%f, end = %fpm%f, alpha = %s" % (c, start_val,
                                                                                     start_sd,
                                                                                     end_val,
                                                                                     end_sd,
                                                                                     str(alpha))
                    if alpha == None:
                        # Can't derive intercept, let later phases fix
                        # it up.
                        return
                    (alphal, alphac, alphah) = alpha
                    if abs(alphal - alphah) < 0.000001:
                        # Treat them as being precisely the same; fix
                        # it up from the massage pass.
                        if -0.01 <= alphal <= 1.01:
                            events.append(("*", pt(alphal)))
                    elif (alphal < alphah) == reverse:
                        # Ascending
                        if -0.01 <= alphal < 1.01:
                            events.append(("L+", pt(alphal)))
                        if -0.01 <= alphac < 1.01:
                            events.append(("C", pt(alphac)))
                        if -0.01 <= alphah < 1.01:
                            events.append(("U+", pt(alphah)))
                    else:
                        # Descending
                        if -0.01 <= alphah < 1.01:
                            events.append(("U-", pt(alphah)))
                        if -0.01 <= alphac < 1.01:
                            events.append(("C", pt(alphac)))
                        if -0.01 <= alphal < 1.01:
                            events.append(("L-", pt(alphal)))

                # Top left to top right
                do_line(lambda a: (a, 1), tl, tls, tr, trs, True)
                # Top right to bottom right
                do_line(lambda a: (1, a), br, brs, tr, trs, False)
                # Bottom right to bottom left
                do_line(lambda a: (a, 0), bl, bls, br, brs, False)
                # Bottom left to top right
                do_line(lambda a: (0, a), bl, bls, tl, tls, True)

                (best_defect, best_massaged) = build_massaged(-1, 0, -1, events, 0, {})
                best_start = -1
                for s in [0, 1]:
                    if best_defect == 0:
                        break
                    (d, m) = build_massaged(s, 0, s, events, 0, {})
                    if d < best_defect:
                        (best_start, best_defect, best_massaged) = (s, d, m)
                if best_defect != 0:
                    sys.stderr.write("Initial sequence %s\n" % str(events))
                    sys.stderr.write("Massaged sequence %s, defect %f, start %d\n" % (str(best_massaged), best_defect, best_start))
                sm_inputs[c] = (best_start, best_massaged)
            # Now render the confidence intervals.
            for (c, (start_state, events)) in sm_inputs.iteritems():
                print "  %%%% Contour %s, start = %d, event sequence = %s" % (c, start_state, str(events))
                in_shape = False
                state = start_state
                def start_shape(pt):
                    print "  \\fill [color=black!50] (%f,%f)" % (scale_x(x + pt[0]), scale_y(y + pt[1]))
                if start_state == 0:
                    start_shape((0, 1))
                    in_shape = True
                for (tag, where) in events:
                    assert -0.01 <= where[0] <= 1.01
                    assert -0.01 <= where[1] <= 1.01
                    if tag == "L+":
                        assert state == -1
                        if not in_shape:
                            in_shape = True
                            start_shape(where)
                        else:
                            print "        -- (%f,%f)" % (scale_x(x + where[0]), scale_y(y + where[1]))
                        state = 0
                    elif tag == "L-":
                        assert state == 0
                        assert in_shape
                        print "        -- (%f,%f)" % (scale_x(x + where[0]), scale_y(y + where[1]))
                        state = -1
                    elif tag == "C":
                        # Center line irrelevant if we're doing confidence intervals
                        assert state == 0
                        continue
                    elif tag == "U+":
                        assert state == 0
                        assert in_shape
                        print "        -- (%f,%f)" % (scale_x(x + where[0]), scale_y(y + where[1]))
                        state = 1
                    elif tag == "U-":
                        assert state == 1
                        if not in_shape:
                            in_shape = True
                            start_shape(where)
                        else:
                            print "        -- (%f,%f)" % (scale_x(x + where[0]), scale_y(y + where[1]))
                        state = 0
                    elif tag == "V":
                        if state == 0:
                            assert in_shape
                            print "        -- (%f, %f)" % (scale_x(x + where[0]), scale_y(y + where[1]))
                        else:
                            # Nothing to do.
                            pass
                    else:
                        abort() # Unknown tag
                if in_shape:
                    print "        -- cycle; %% %f" % c
            # And now the contours themselves
            for (c, (start_state, events)) in sm_inputs.iteritems():
                decoration = contour_labels.get(c, ("", ""))[0]
                last = None
                state = start_state
                for (tag, where) in events:
                    if tag == "L+":
                        assert state == -1
                        state = 0
                    elif tag == "L-":
                        assert state == 0
                        state = -1
                    elif tag == "C":
                        assert state == 0
                        if last == None:
                            last = where
                        else:
                            (x0, x1, y0, y1) = (scale_x(x + last[0]),
                                                scale_x(x + where[0]),
                                                scale_y(y + last[1]),
                                                scale_y(y + where[1]))
                            print "  \\draw [%s] (%f, %f) -- (%f, %f);" % (decoration, x0, y0, x1, y1)
                            # Do we need to update our estimates of
                            # where the label goes?  Defect is
                            # square distance from point to the
                            # diagonal, and we try to get as close as
                            # possible.
                            if c in contour_labels:
                                def defect(x, y):
                                    return x ** 2 + y ** 2 - (x + y) ** 2 / 2
                                (xa,ya) = ((x0 + x1)/2 - extent[0][0], (y0 + y1)/2 - extent[0][1])
                                newDist = defect(xa, ya)
                                if not label_posns.has_key(c):
                                    # Hack: all that matters is that it's bigger than newDist
                                    oldDist = newDist + 1
                                else:
                                    oldLabel = label_posns[c]
                                    oldDist = defect(oldLabel[0], oldLabel[1])
                                if newDist < oldDist:
                                    bearing = math.atan2(y0 - y1, x0 - x1)
                                    label_posns[c] = (xa, ya, bearing)
                            last = None
                    elif tag == "U+":
                        assert state == 0
                        state = 1
                    elif tag == "U-":
                        assert state == 1
                        state = 0
                    elif tag == "V":
                        # Nothing to do.
                        continue
                    else:
                        abort() # Unknown tag
                assert last == None

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
        print "  \\node at (%f, %f) [rotate=%f%s] {\small %s};" % (x + extent[0][0], y + extent[0][1], b, contour_labels[k][1], contour_labels[k][2])
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
             [1.0, 10**.5, 10.0, 10 * 10**.5, 100.0, 100 * 10**.5],
             {1.0: ("", "", "1s"),
              10.0: ("", "", "10s"),
              100.0: ("", "", "100s")})
contour_map( ((figwidth+sep, 0), (figwidth * 2 + sep, figheight)), mems, suppress, 10, timeouts, ooms,
             [ 100000000, 300000000, 1000000000, 2000000000],
             {(100000000): ("", "", "100MB"),
              (300000000): ("", "", "300MB"),
              (1000000000): ("", "", "1GB"),
              (2000000000): ("dashed","", "2GB")})

print "\\end{tikzpicture}"
