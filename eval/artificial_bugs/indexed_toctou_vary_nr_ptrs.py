#! /usr/bin/env python

import sys
import math

fig_width = 14.0
fig_height = 8.0
b_width = 0.2

data_dir = "special/indexed_toctou_vary_nr_ptrs_%s" % sys.argv[1]
abscissae = [10,20,30,40,50,60,70,80,90,100,150,200,250,300,350,400,450,500,750,1000,2000,3000,4000,5000]

max_time = 0
data = {}
for a in abscissae:
    try:
        f = file("%s/nr_ptrs=%d" % (data_dir, a), "r")
    except:
        continue
    series = map(lambda x: float(x.strip()), f.xreadlines())
    f.close()
    series.sort()
    mean = sum(series) / len(series)
    if mean > max_time:
        max_time = mean
    p75 = series[(len(series)*3)/4]
    if p75 > max_time:
        max_time = p75
    sd = (sum([(x - mean)**2 for x in series]) / (len(series) * (len(series) - 1))) ** .5
    data[a] = { "min": min(series),
                "max": max(series),
                "mean": mean,
                "sd": sd,
                "50": series[len(series)/2],
                "25": series[len(series)/4],
                "75": p75 }

def sane_round(t):
    if t == 0:
        return (0,"0")
    nr_digits = int(math.log(t) / math.log(10))
    natural_max = float(10 ** nr_digits)
    first_digit = int(t/natural_max)
    if nr_digits < -4 or nr_digits > 4:
        return (first_digit * 10 ** nr_digits,
                "$%d {\\times} 10^{%d}$" % (first_digit, nr_digits))
    elif nr_digits >= 0:
        return (first_digit * 10 ** nr_digits,
                ("%d" % first_digit) + "0" * nr_digits)
    else:
        return (first_digit * 10 ** nr_digits,
                "0." + ("0" * (-nr_digits - 1)) + ("%d" % first_digit))

def abs_to_x(a):
    return math.log(a / float(abscissae[0])) / math.log(abscissae[-1] / float(abscissae[0])) * fig_width
def time_to_y(t):
    if t < 0.1:
        return 0
    return math.log(t / 0.1) / math.log(max_time / 0.1) * fig_height

print "\\begin{tikzpicture}"
# Draw axes
print "  \\draw[->] (0,0) -- (0,%f);" % fig_height
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
    yticks = [(0.1, "0.1"), (0.25, "0.25"), (0.5, "0.5"),
              (1, "1.0"), (2.5, "2.5"), (5, "5.0")]
else:
    yticks = [(0.1,"0.1"), (1, "1.0"),
              (10, "10"), (100, "100"),
              (1000, "1000")]
for (t, label) in yticks:
    print "  \\node at (0,%f) [left] {%s};" % (time_to_y(t), label)
    print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (time_to_y(t), fig_width, time_to_y(t))
print "  \\node at (-12pt,%f) [rotate=90,left = 1, anchor = north] {Time to reproduce, seconds};" % (fig_height / 2)

decorations = { "mean": "[color=red!50]",
                "25": "[dashed]",
                "50": "",
                "75": "[dotted]" }
# Plot the data
for line in ["mean", "25", "50", "75"]:
    print "  \\draw%s (0,0)" % decorations[line]
    for a in abscissae:
        if data.has_key(a):
            print "        -- (%f,%f)" % (abs_to_x(a), time_to_y(data[a][line]))
    print "        ;"

# Add some error bars to the mean
decoration = decorations["mean"]
for a in abscissae:
    if not data.has_key(a):
        continue
    x = abs_to_x(a)
    d = data[a]
    upper_y = time_to_y(d["mean"] + d["sd"])
    lower_y = time_to_y(d["mean"] - d["sd"])
    print "  \\draw%s (%f, %f) -- (%f, %f);" % (decoration, x - 0.1, upper_y, x + 0.1, upper_y)
    print "  \\draw%s (%f, %f) -- (%f, %f);" % (decoration, x - 0.1, lower_y, x + 0.1, lower_y)
    print "  \\draw%s (%f, %f) -- (%f, %f);" % (decoration, x, upper_y, x, lower_y)
    
print "  \\node at (%f,%f) [below right] {\\shortstack[l]{" % (0, fig_height)
labels = {"mean": "Mean",
          "25": "$25^{th}$ percentile",
          "50": "Median",
          "75": "$75^{th}$ percentile"}
isFirst = True
for l in ["mean", "25", "50", "75"]:
    if not isFirst:
        print "\\\\"
    isFirst = False
    print "        \\raisebox{1mm}{\\tikz{\\draw%s (0,0) -- (1,0);}} %s" % (decorations[l], labels[l]),
print
print "  }};"

print "\\end{tikzpicture}"
