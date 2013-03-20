#! /usr/bin/env python

import sys

from util import *
import util
util.fig_width = 14

print_preamble()
series = [("multi_threads.crash_times_data", "No enforcer"),
          ("multi_threads~0.crash_times_data", "Fair lock enforcer"),
          ("special/multi_threads_unfair.crash_times_data", "Unfair lock enforcer")]
i = 0
for (fname, _descr) in series:
    s = read_series(fname)
    print "  \\draw%s (0,0) " % decorations[i % len(decorations)],
    last_y = 0
    for (x,y) in s[0]:
        last_y = y
        if x < 0.1:
            x = 0.1
        lp = "(%f,%f)" % (time_to_x(x), perc_to_y(y))
        print " -- %s" % lp,
    print " -- (%f, %f);" % (time_to_x(180), perc_to_y(last_y))
    i += 1
print "\\end{tikzpicture}"
