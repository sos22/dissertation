#! /usr/bin/env python

import sys
import math
import random

fig_width = 13.0
fig_height = 8.0
b_width = 0.2
nr_replicates = 10000
mintime = 0.01

data_dir = "special/indexed_toctou_vary_nr_ptrs_%s" % sys.argv[1]
abscissae = [10,20,30,40,50,60,70,80,90,100,150,200,250,300,350,400,450,500,750,1000,2000,3000,4000,5000]

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

data = {}
for a in abscissae:
    try:
        f = file("%s/nr_ptrs=%d" % (data_dir, a), "r")
    except:
        continue
    series = map(lambda x: float(x.strip()), f.xreadlines())
    f.close()

    series.sort()

    def calc_stats(data):
        return {"mean": sum(data) / float(len(data)),
                "p25": quantile(data, 0.25),
                "p50": quantile(data, 0.50),
                "p75": quantile(data, 0.75),
                }
    data[a] = bootstrap_stats(series, calc_stats)

max_time = max([max(max(k.itervalues())) for k in data.itervalues()])

def abs_to_x(a):
    return math.log(a / float(abscissae[0])) / math.log(abscissae[-1] / float(abscissae[0])) * fig_width
def time_to_y(t):
    if t < mintime:
        return 0
    return math.log(t / mintime) / math.log(max_time / mintime) * fig_height

print "\\begin{tikzpicture}"
# Draw axes
print "  \\draw[->] (-.1,0) -- (-.1,%f);" % fig_height
print "  \\draw[->] (0,0) -- (%f,0);" % fig_width
# x ticks
for (a,label) in [(10, "10"), (20, "20"),
                  (40, "40"),
                  (100, "100"), (200, "200"),
                  (400, "400"),
                  (1000, "1000"), (2000, "2000"),
                  (4000, "4000")]:
    print "  \\node at (%f,0) [below] {%s};" % (abs_to_x(a), label)
    print "  \\draw[color=black!10] (%f,0) -- (%f,%f);" % (abs_to_x(a), abs_to_x(a), fig_height)
print "  \\node at (%f,-12pt) [below] {NR\_PTRS};" % (fig_width/2)

# y ticks
if sys.argv[1] == "enforcer":
    yticks = [(0.01, "0.01"), (0.1, "0.1"),
              (0.25, "0.25"), (0.5, "0.5"),
              (1, "1.0"), (2.5, "2.5"), (5, "5.0")]
else:
    yticks = [(0.01, "0.01"), (0.1,"0.1"), (1, "1.0"),
              (10, "10"), (100, "100"),
              (1000, "1000")]
for (t, label) in yticks:
    print "  \\node at (-.1,%f) [left] {%s};" % (time_to_y(t), label)
    print "  \\draw[color=black!10] (-.1,%f) -- (%f,%f);" % (time_to_y(t), fig_width, time_to_y(t))
print "  \\node at (-14pt,%f) [rotate=90,left = 1, anchor = north] {Time to reproduce, seconds};" % (fig_height / 2)

for a in abscissae:
    if not data.has_key(a):
        continue
    mean = data[a]["mean"]
    p25 = data[a]["p25"]
    p50 = data[a]["p50"]
    p75 = data[a]["p75"]
    l = abs_to_x(a)-.1
    r = abs_to_x(a)+.1
    print "\\fill [color=black!50] (%f,%f) rectangle (%f,%f);" % (l, time_to_y(p25[0]),
                                                                  r, time_to_y(p25[2]))
    print "\\fill [color=black!50] (%f,%f) rectangle (%f,%f);" % (l, time_to_y(p50[0]),
                                                                  r, time_to_y(p50[2]))
    print "\\fill [color=black!50] (%f,%f) rectangle (%f,%f);" % (l, time_to_y(p75[0]),
                                                                  r, time_to_y(p75[2]))
    print "\\draw (%f,%f) -- (%f,%f);" % (abs_to_x(a), time_to_y(mean[0]),
                                          abs_to_x(a), time_to_y(mean[2]))
    print "\\draw (%f,%f) -- (%f,%f);" % (abs_to_x(a)-.05, time_to_y(mean[2]),
                                          abs_to_x(a)+.05, time_to_y(mean[2]))
    print "\\draw (%f,%f) -- (%f,%f);" % (abs_to_x(a)-.05, time_to_y(mean[0]),
                                          abs_to_x(a)+.05, time_to_y(mean[0]))
    
    print "\\draw (%f,%f) rectangle (%f,%f);" % (abs_to_x(a)-.1,
                                                 time_to_y(p25[1]),
                                                 abs_to_x(a)+.1,
                                                 time_to_y(p75[1]))
    print "\\draw (%f,%f) -- (%f,%f);" % (abs_to_x(a)-.1, time_to_y(p50[1]),
                                          abs_to_x(a)+.1, time_to_y(p50[1]))
    print "\\draw (%f,%f) -- (%f,%f);" % (abs_to_x(a)-.05, time_to_y(mean[1])-.05,
                                          abs_to_x(a)+.05, time_to_y(mean[1])+.05)
    print "\\draw (%f,%f) -- (%f,%f);" % (abs_to_x(a)+.05, time_to_y(mean[1])-.05,
                                          abs_to_x(a)-.05, time_to_y(mean[1])+.05)

print "\\end{tikzpicture}"
