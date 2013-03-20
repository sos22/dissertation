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
    plot_series(s[0], i)
    i += 1
print "\\end{tikzpicture}"
