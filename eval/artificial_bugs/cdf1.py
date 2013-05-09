#! /usr/bin/env python

import sys
import math

figheight = 7.0
figwidth = 15.0
sep = 1.0
chartwidth = (figwidth - 2 * sep) / 3
mintime = 0.1
maxtime = 180

def time_to_x(time, chart_idx):
    return chart_idx * (chartwidth + sep) + math.log(time/mintime) / math.log(maxtime/mintime) * chartwidth
def frac_to_y(frac):
    return figheight * frac

print "\\begin{tikzpicture}"

print "  %% X axis"
for i in [0,1,2]:
    print "  \\draw[->] (%f, %f) -- (%f, %f); " % (time_to_x(mintime, i), 0, time_to_x(maxtime, i), 0)
    for time_label in ["0.1", "0.5", "1", "2", "4", "8", "16", "32", "64", "128", "180"]:
        x = time_to_x(float(time_label), i)
        print "  \\node at (%f, %f) [below] {%s};" % (x, 0, time_label)
        print "  \\draw[color=black!10] (%f, %f) -- (%f, %f);" % (x, 0, x, figheight)

print "  %% Y axis"
print "  \\draw[->] (%f, %f) -- (%f, %f);" % (0, 0, 0, figheight)
for p in xrange(0, 101, 20):
    y = frac_to_y(p / 100.0)
    print "  \\node at (%f, %f) [left] {%d\\%%};" % (0, y, p)
    print "  \\draw[color=black!10] (%f, %f) -- (%f, %f)" % (0, y, figwidth, y)

series = {".crash_times_data": ("", "Without enforcer"), "~0.crash_times_data": ("dashed", "With enforcer")}
for (idx, name) in [(0,"indexed_toctou"), (1,"multi_variable"), (2,"double_free")]:
    for (name2, (decoration, _)) in series.iteritems():
        f = file(name + name2)
        d = []
        nr_timeouts = 0
        below_cutoff = 0
        for l in f.xreadlines():
            w = l.split()
            if w[-1] == "T":
                nr_timeouts+= 1
            else:
                w = float(w[0])
                if w < mintime:
                    below_cutoff += 1
                elif w > maxtime:
                    nr_timeouts += 1
                else:
                    d.append(w)
        f.close()
        tot = float(nr_timeouts + below_cutoff + len(d))
        print "  %%%% Series %s%s" % (name, name2)
        print "  \\draw [%s] (%f, %f)" % (decoration, time_to_x(mintime, idx), frac_to_y(below_cutoff / tot))
        cntr = below_cutoff
        for datum in d:
            cntr += 1
            print "        -- (%f, %f)" % (time_to_x(datum, idx), frac_to_y(cntr / tot))
        print "        -- (%f, %f);" % (time_to_x(maxtime, idx), frac_to_y(1))

print "\\end{tikzpicture}"

print "\\centerline{"
print "  \\hfill"
for (decoration, descr) in series.itervalues():
    print "  \\raisebox{1mm}{\\tikz{\\draw [%s] (0, 0) -- (1, 0);}} %s" % (decoration, descr)
    print "  \\hfill"
print "}"
