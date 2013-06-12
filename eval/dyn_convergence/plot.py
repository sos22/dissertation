#! /usr/bin/env python

import sys
import math

if len(sys.argv) == 3 and sys.argv[2] == "narrow":
    fig_width = 5.2
    fig_height = 5.0
    narrow = True
else:
    fig_width = 13.5
    fig_height = 5.0
    narrow = False
if len(sys.argv) == 3 and sys.argv[2] == "scale":
    scale = True
else:
    scale = False

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
        if scale:
            t /= 1000
        if t > max_time:
            max_time = t
        if min_time == None or min_time > t:
            min_time = t
        cur_series.append((t, float(w[1])))
series.append(cur_series)

def round_up(what):
    nr_digits = int(math.log(what) / math.log(10))
    b = what - what % (10 ** nr_digits)
    if what != b:
        b += 10 ** nr_digits
    sys.stderr.write("round_up(%f) -> %f\n" % (what, b))
    return b

t_width = int(round_up(max_time - min_time))
if t_width == 200:
    t_width = 175
    step = 25
elif t_width == 300:
    if narrow:
        t_width = 250
        step = 50
    else:
        t_width = 275
        step = 25
elif t_width == 1000:
    step = 200
elif t_width == 500:
    if narrow:
        step = 100
    else:
        step = 50
elif t_width == 700:
    step = 50
    t_width = 650
sys.stderr.write("t_width %d, step %d\n" % (t_width, step))

def pt((x, y)):
    return ((x - min_time) / t_width * fig_width, y * fig_height)

print "\\begin{tikzpicture}"
print "  \\fill [color=white] (0,0) rectangle (%f,%f);" % (fig_width, fig_height)
print "  \\draw[->] (0,0) -- (%f,0);" % fig_width
print "  \\draw[->] (0,0) -- (0,%f);" % fig_height
for i in xrange(0, 11):
    print "  \\node at (0,%f) [left] {%d\\%%};" % (i/10.0 * fig_height, i * 10)

for t in xrange(0, t_width + 1, step):
    print "  \\node at (%f, 0) [below] {%d};" % (float(t)/t_width * fig_width, t)

print "  \\node at (%f, %f) [below] {Time in seconds};" % (fig_width / 2, -0.5)

last = "(0,0)"
for s in series:
    print "  \\draw (%f, %f)" % pt(s[0])
    for p in s[1:]:
        print "        -- (%f, %f)" % pt(p)
        last = str(pt(p))
    print "  ;"

for s in series[1:]:
    x = (s[0][0] - min_time) / t_width * fig_width
    print "  \\draw[dashed,color=black!50] (%f,0) -- (%f,%f);" % (x, x, fig_height)

print "\\end{tikzpicture}"
