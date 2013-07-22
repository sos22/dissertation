#! /usr/bin/env python

import sys
import math
import random

figwidth = 12.8
figheight = 7

nr_replicates = 1000
b_width = 0.01
c_width = 0.005

mintime = 0.175
maxtime = 0.35

abscissae = range(0,81,5)[1:]
time_grads = ["0.%d" % x for x in xrange(175, 360, 25)]

def count_to_x(count):
    return count / 80.0
def time_to_y(time):
    return (time  - mintime) / (maxtime - mintime)


with_enforcer = {}
without_enforcer = {}

inp = file("repro_times")
for l in inp.xreadlines():
    w = l.split()
    key = int(w[1]) + 1
    val = float(w[2])
    if w[0] == "with":
        with_enforcer.setdefault(key, []).append(val)
    elif w[0] == "without":
        without_enforcer.setdefault(key, []).append(val)
    else:
        abort()

output = file("repro_times.tex", "w")
output.write("\\begin{tikzpicture}\n")
output.write("\\begin{scope}[xscale=%f,yscale=%f]\n" % (figwidth, figheight))
output.write("\\begin{pgfonlayer}{bg}\n")
output.write("\\fill [color=white] (0,0) rectangle (1,1);\n")
for abs in abscissae:
    output.write("\\draw [color=black!10] (%f,0) -- (%f,1);\n" % (count_to_x(abs), count_to_x(abs)))
for t in time_grads:
    y = time_to_y(float(t))
    output.write("\\draw [color=black!10] (0,%f) -- (1,%f);\n" % (y, y))
output.write("\\end{pgfonlayer}\n")

output.write("\\begin{pgfonlayer}{fg}\n")
output.write("\\draw[->] (0,0) -- (1,0);\n")
output.write("\\draw[->] (0,0) -- (0,1);\n")
for abs in abscissae:
    output.write("\\node at (%f,0) [below] {%d};\n" % (count_to_x(abs), abs))
output.write("\\node at (0.5,-.1) [below] {Number of edges, $2N$};\n")
for t in time_grads:
    output.write("\\node at (0,%f) [left] {%s};\n" % (time_to_y(float(t)), t))
output.write("\\node at (-.15,.5) [below,rotate=90] {Time to reproduce, seconds};\n")
output.write("\\end{pgfonlayer}\n")

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
            }

d = {}
for (k, v) in with_enforcer.iteritems():
    x = v[10:]
    x.sort()
    d[k] = bootstrap_stats(x, calc_stats)

def draw_box(output, l, r, box):
    output.write("\\begin{pgfonlayer}{bg}\n")
    output.write("\\fill [color=white] (%f,%f) rectangle (%f,%f);\n" % (l,
                                                                        time_to_y(box[0]),
                                                                        r,
                                                                        time_to_y(box[2])))
    output.write("\\end{pgfonlayer}\n")
    output.write("\\draw (%f,%f) rectangle (%f,%f);\n" % (l,
                                                          time_to_y(box[0]),
                                                          r,
                                                          time_to_y(box[2])))
    output.write("\\draw (%f,%f) -- (%f,%f);\n" % (l, time_to_y(box[1]),
                                                   r, time_to_y(box[1])))

for (k, v) in d.iteritems():
    mean = v["mean"]
    x = count_to_x(k)
    l = x-b_width/2
    r = x+b_width/2
    
    l = x - c_width/2
    r = x + c_width/2
    output.write("\\draw (%f,%f) -- (%f,%f);\n" % (x, time_to_y(mean[0]),
                                                   x, time_to_y(mean[2])))
    output.write("\\draw (%f,%f) -- (%f,%f);\n" % (l, time_to_y(mean[2]),
                                                   r, time_to_y(mean[2])))
    output.write("\\draw (%f,%f) -- (%f,%f);\n" % (l, time_to_y(mean[0]),
                                                 r, time_to_y(mean[0])))
    b = time_to_y(mean[1]) - c_width/2
    t = time_to_y(mean[1]) + c_width/2
    output.write("\\draw (%f,%f) -- (%f,%f);\n" % (l, b, r, t))
    output.write("\\draw (%f,%f) -- (%f,%f);\n" % (r, b, l, t))

output.write("\\end{scope}\n")
output.write("\\end{tikzpicture}\n")


