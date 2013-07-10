#! /usr/bin/env python

import sys
import math
import random

fig_width = 13.0
fig_height = 8.0
b_width = 0.1
c_width = 0.05
nr_replicates = 1000
mintime = 0.01
maxtime = 10000.0
min_np = 1.
max_np = 320000.

yticks = [(0.01, "0.01"), (0.03, "0.03"),
          (0.1, "0.1"), (0.3, "0.3"),
          (1, "1.0"), (3.0, "3"),
          (10, "10"), (30.0, "30"),
          (100.0, "100"), (300.0, "300"),
          (1000.0, "1000"), (3000.0, "3000"),
          (10000.0, "10000")]

if sys.argv[1] == "enforcer":
    enforcer = True
else:
    enforcer = False

def quantile(data, q):
    idx = q * len(data)
    idx1 = int(idx)
    idx2 = idx1 + 1
    if idx2 >= len(data):
        return data[-1]
    return data[idx1] * (idx - idx1) + data[idx2] * (1 - idx + idx1)

def gen_replicate(data):
    return list(sorted([random.choice(data) for _ in xrange(len(data))]))

def bootstrap_stats(data, stat):
    base = stat(data)
    replicates = [stat(gen_replicate(data)) for _ in xrange(nr_replicates)]
    res = {}
    for k in base.iterkeys():
        s = list([r[k] for r in replicates])
        s.sort()
        res[k] = (quantile(s, 0.05), base[k], quantile(s, 0.95))
    return res

def calc_stats(data):
    return {"mean": sum(data) / float(len(data)),
            "p25": quantile(data, 0.25),
            "p50": quantile(data, 0.50),
            "p75": quantile(data, 0.75),
            }

data = {}
with open("special/indexed_toctou_vary_nr_ptrs.results") as f:
    for l in f.xreadlines():
        w = l.split()
        if not w[0] in ["with", "without"]:
            sys.stderr.write("Unexpected keyword %s in input\n" % w[0])
            sys.exit(1)
        if (w[0] == "with") != enforcer:
            continue
        key = int(w[1])
        time = float(w[2])
        if not data.has_key(key):
            data[key] = []
        data[key].append(time)
d = {}
for (k, v) in data.iteritems():
    x = v[10:]
    x.sort()
    d[k] = bootstrap_stats(x, calc_stats)
data = d
del d

abscissae = data.keys()
abscissae.sort()

def abs_to_x(a):
    return math.log(a / min_np) / math.log(max_np / min_np) * fig_width
def time_to_y(t):
    if t < mintime:
        return 0
    return math.log(t / mintime) / math.log(maxtime / mintime) * fig_height

print "\\begin{tikzpicture}"
print "  \\fill [color=white] (%f,0) rectangle (%f,%f);" % (-b_width/2, fig_width+b_width/2, fig_height);
# Draw axes
print "  \\begin{pgfonlayer}{fg}"
print "    \\draw[->] (%f,0) -- (%f,%f);" % (-b_width/2, -b_width/2, fig_height)
print "    \\draw[->] (0,0) -- (%f,0);" % fig_width
print "  \\end{pgfonlayer}"
# x ticks
for (a,label) in [(1,"1"), (3, "3"),
                  (10, "10"), (30, "30"),
                  (100, "100"), (300, "300"),
                  (1000, "1000"), (3000, "3000"),
                  (10000, "1e4"), (30000, "3e4"),
                  (100000, "1e5"), (300000, "3e5")]:
    print "  \\node at (%f,0) [below] {%s};" % (abs_to_x(a), label)
    print "  \\draw[color=black!10] (%f,0) -- (%f,%f);" % (abs_to_x(a), abs_to_x(a), fig_height)
print "  \\node at (%f,-12pt) [below] {NR\_PTRS};" % (fig_width/2)

# y ticks
for (t, label) in yticks:
    print "  \\node at (%f,%f) [left] {%s};" % (-b_width/2, time_to_y(t), label)
    print "  \\draw[color=black!10] (%f,%f) -- (%f,%f);" % (-b_width/2, time_to_y(t), fig_width+b_width/2, time_to_y(t))
print "  \\node at (-14pt,%f) [rotate=90,left = 1, anchor = north] {Time to reproduce, seconds};" % (fig_height / 2)

for a in abscissae:
    if not data.has_key(a):
        continue
    mean = data[a]["mean"]
    p25 = data[a]["p25"]
    p50 = data[a]["p50"]
    p75 = data[a]["p75"]
    l = abs_to_x(a)-b_width/2
    r = abs_to_x(a)+b_width/2
    print "\\fill [color=black!50] (%f,%f) rectangle (%f,%f);" % (l, time_to_y(p25[0]),
                                                                  r, time_to_y(p25[2]))
    print "\\fill [color=black!50] (%f,%f) rectangle (%f,%f);" % (l, time_to_y(p50[0]),
                                                                  r, time_to_y(p50[2]))
    print "\\fill [color=black!50] (%f,%f) rectangle (%f,%f);" % (l, time_to_y(p75[0]),
                                                                  r, time_to_y(p75[2]))
    
    print "\\draw (%f,%f) rectangle (%f,%f);" % (l,
                                                 time_to_y(p25[1]),
                                                 r,
                                                 time_to_y(p75[1]))
    print "\\draw (%f,%f) -- (%f,%f);" % (l, time_to_y(p50[1]),
                                          r, time_to_y(p50[1]))
    l = abs_to_x(a) - c_width/2
    r = abs_to_x(a) + c_width/2
    print "\\draw (%f,%f) -- (%f,%f);" % (abs_to_x(a), time_to_y(mean[0]),
                                          abs_to_x(a), time_to_y(mean[2]))
    print "\\draw (%f,%f) -- (%f,%f);" % (l, time_to_y(mean[2]),
                                          r, time_to_y(mean[2]))
    print "\\draw (%f,%f) -- (%f,%f);" % (l, time_to_y(mean[0]),
                                          r, time_to_y(mean[0]))
    b = time_to_y(mean[1]) - c_width/2
    t = time_to_y(mean[1]) + c_width/2
    print "\\draw (%f,%f) -- (%f,%f);" % (l, b, r, t)
    print "\\draw (%f,%f) -- (%f,%f);" % (r, b, l, t)

print "\\end{tikzpicture}"
