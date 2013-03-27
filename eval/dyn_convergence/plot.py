#! /usr/bin/env python

import sys

fig_width = 13
fig_height = 7

f = file(sys.argv[1], "r")

series = []
cur_series = None
max_time = 0
min_time = None
for l in f.xreadlines():
    w = l.split()
    if w[0] == "new_series":
        if cur_series != None:
            series.append(cur_series)
        cur_series = []
    else:
        t = float(w[0])
        if t > max_time:
            max_time = t
        if min_time == None or min_time > t:
            min_time = t
        cur_series.append((t, float(w[1])))
series.append(cur_series)

def pt((x, y)):
    return ((x - min_time) / (max_time - min_time) * fig_width, y * fig_height)

print "\\begin{tikzpicture}"
print "  \\draw[->] (0,0) -- (%f,0);" % fig_width
print "  \\draw[->] (0,0) -- (0,%f);" % fig_height
for i in xrange(0, 11):
    print "  \\node at (0,%f) [left] {%d\\%%};" % (i/10.0 * fig_height, i * 10)
for t in xrange(0, 1001, 100):
    print "  \\node at (%f, 0) [below] {%d};" % (t/1000.0 * fig_width, t)
print "  \\node at (%f, %f) [below] {Time in seconds};" % (fig_width / 2, -1)

last = "(0,0)"
for s in series:
    print "  \\draw (%f, %f)" % pt(s[0])
    for p in s[1:]:
        print "        -- (%f, %f)" % pt(p)
        last = str(pt(p))
    print "  ;"

for s in series[1:]:
    x = (s[0][0] - min_time) / (max_time - min_time) * fig_width
    print "  \\draw[dashed,color=black!50] (%f,0) -- (%f,%f);" % (x, x, fig_height)

print "\\end{tikzpicture}"
