#! /usr/bin/env python

import sys
import math
import random
import decimal

figheight = 4.5
figwidth = 14.0
sep = 0.7
chartwidth = (figwidth - 2 * sep) / 3
mintime = 0.1
maxtime = 180
nr_replicates = 10000

def time_to_x(time, chart_idx):
    return chart_idx * (chartwidth + sep) + math.log(time/mintime) / math.log(maxtime/mintime) * chartwidth
def frac_to_y(frac):
    return figheight * frac

bug_names = {"indexed_toctou": "\\bugname{toctou}",
             "multi_variable": "\\bugname{multi\_variable}",
             "double_free": "\\bugname{double\_free}"}
print "\\centerline{"
print "\\begin{tikzpicture}"

x_labels = ["0.1", "1", "10", "180"]
y_labels = map(str, xrange(0, 101, 20))

print "  %% Grid"
for idx in [0,1,2]:
    print "\\fill [color=white] (%f,0) rectangle (%f,%f);" % (time_to_x(mintime, idx), time_to_x(maxtime, idx), figheight)
    for x_label in x_labels:
        x = time_to_x(float(x_label), idx)
        print "  \\draw [color=black!10] (%f, %f) -- (%f, %f);" % (x, 0, x, figheight)
for y_label in y_labels:
    y = frac_to_y(float(y_label) / 100)
    print "  \\draw [color=black!10] (%f, %f) -- (%f, %f);" % (0, y, figwidth, y)
print "  %% X axis"
for i in [0,1,2]:
    print "  \\draw[->] (%f, %f) -- (%f, %f); " % (time_to_x(mintime, i), 0, time_to_x(maxtime, i), 0)
    for idx in xrange(len(x_labels)):
        x = time_to_x(float(x_labels[idx]), i)
        where = "below"
        print "  \\node at (%f, %f) [%s] {%s};" % (x, 0, where, x_labels[idx])
print "  \\node at (%f, -18pt) [below] {Time to reproduce};" % (figwidth / 2)

print "  %% Y axis"
print "  \\draw[->] (%f, %f) -- (%f, %f);" % (0, 0, 0, figheight)
for idx in xrange(len(y_labels)):
    y = frac_to_y(float(y_labels[idx]) / 100.0)
    where = "left"
    print "  \\node at (%f, %f) [%s] {%s\\%%};" % (0, y, where, y_labels[idx])

series = {".crash_times_data": ("", "Without enforcer"), "~0.crash_times_data": ("dashed", "With enforcer")}
for (idx, name) in [(0,"indexed_toctou"), (1,"multi_variable"), (2,"double_free")]:
    print "  \\node at (%f, %f) [above] {%s};" % (idx * (chartwidth + sep) + (chartwidth / 2), figheight, bug_names[name])
    data = {}
    for name2 in series.iterkeys():
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
        d.sort()
        data[name2] = (d, nr_timeouts, below_cutoff)
    # Start with the error region.
    for name2 in series:
        (d, nr_timeouts, below_cutoff) = data[name2]
        tot = float(nr_timeouts + below_cutoff + len(d))

        dkw_bound = (-math.log(0.9/2) / (2.0 * tot)) ** .5

        prop_low = max(below_cutoff / tot - dkw_bound, 0.0)
        prop_high = min(below_cutoff / tot + dkw_bound, 1.0)
        print "  \\fill [color=black!50] (%f, %f) -- (%f, %f)" % (time_to_x(mintime, idx),
                                                                  frac_to_y(prop_low),
                                                                  time_to_x(mintime, idx),
                                                                  frac_to_y(prop_high))
        for (cntr, datum) in enumerate(d):
            prop = min((cntr + below_cutoff) / tot + dkw_bound, 1.0)
            print "        -- (%f, %f)" % (time_to_x(datum, idx), frac_to_y(prop))
        print "        -- (%f, %f) -- (%f, %f) -- (%f, %f)" % (time_to_x(maxtime, idx), frac_to_y(1),
                                                               time_to_x(maxtime, idx), frac_to_y((len(d) - 1 + below_cutoff) / tot - dkw_bound),
                                                               time_to_x(d[-1], idx), frac_to_y((len(d) - 1 + below_cutoff) / tot - dkw_bound))
        for (cntr, datum) in reversed(list(enumerate(d))):
            prop = max((cntr + below_cutoff) / tot - dkw_bound, 0.0)
            print "        -- (%f, %f)" % (time_to_x(datum, idx), frac_to_y(prop))
        print "        -- cycle;"

        # Main series
    for (name2, (decoration, _)) in series.iteritems():
        (d, nr_timeouts, below_cutoff) = data[name2]
        tot = float(nr_timeouts + below_cutoff + len(d))

        print "  \\draw [%s] (%f, %f)" % (decoration, time_to_x(mintime, idx), frac_to_y(below_cutoff / tot))
        cntr = below_cutoff
        for datum in d:
            cntr += 1
            print "        -- (%f, %f)" % (time_to_x(datum, idx), frac_to_y(cntr / tot))
        print "        -- (%f, %f);" % (time_to_x(maxtime, idx), frac_to_y(cntr / tot))

print "\\end{tikzpicture}"
print "}"

print "\\centerline{"
print "  \\hfill"
for (decoration, descr) in series.itervalues():
    print "  \\raisebox{1mm}{\\tikz{\\draw [%s] (0, 0) -- (1, 0);}} %s" % (decoration, descr)
    print "  \\hfill"
print "}"
print "\\vspace{12pt}"

def nr_digits(x):
    x = abs(x)
    lx = math.log(x,10)
    if lx < -3:
        return -3
    elif lx < 0:
        return int(lx - 0.9999)
    else:
        return int(lx)

def sane_round(thing, decimal_places):
    # Annoyingly, python's decimal library can't quantize to whole
    # powers of ten, only reciprocal ones.  Work around it.
    if decimal_places < 0:
        return decimal.Decimal(str(thing)).quantize(decimal.Decimal("0." + "0" * (-decimal_places-1) + "1"))
    return decimal.Decimal(str(thing / (10 ** decimal_places))).quantize(decimal.Decimal("1.")) * (10 ** decimal_places)
def get_quantile(d, q):
    assert q>= 0 and q <= 1
    idx = q * len(d)
    idx0 = int(idx)
    idx1 = idx0+1
    if idx1 >= len(d):
        assert idx1 == len(d) or idx1 == len(d)+1
        return d[-1]
    idx -= idx0
    return (d[idx0] * (1 - idx)) + (d[idx1] * idx)

def bootstrap_quantile(data, q):
    def gen_replicate():
        rs = map(lambda x: random.choice(data), data)
        rs.sort()
        return get_quantile(rs, q)
    replicate_stats = map(lambda x: gen_replicate(), xrange(nr_replicates))
    replicate_stats.sort()
    lower = get_quantile(replicate_stats, 0.05)
    upper = get_quantile(replicate_stats, 0.95)
    nd = nr_digits(upper - lower)
    lower2 = sane_round(lower, nd)
    upper2 = sane_round(upper, nd)
    return "$[%s,%s]_{%d}^{%d}$" % (lower2, upper2,
                                    nr_replicates,
                                    len(data))

def bootstrap_mean(data):
    def gen_replicate():
        rs = map(lambda x: random.choice(data), data)
        rs.sort()
        return sum(rs) / float(len(rs))
    replicate_stats = map(lambda x: gen_replicate(), xrange(nr_replicates))
    replicate_stats.sort()
    lower = get_quantile(replicate_stats, 0.05)
    upper = get_quantile(replicate_stats, 0.95)
    return "$[%f,%f]_{%d}^{%d}$" % (lower, upper,
                                    nr_replicates,
                                    len(data))

def clt_mean(d):
    mean = sum(d) / len(d)
    sd = (sum([(x - mean) ** 2 for x in d]) / len(d)) ** .5
    sd_mean = sd / ((len(d) - 1) ** .5)
    nd = nr_digits(sd_mean)
    mean2 = sane_round(mean, nd)
    sd_mean2 = sane_round(sd_mean, nd)
    return "%s $\\pm_{\mu}^{%d}$ %s" % (mean2, len(d), sd_mean2)

# Summary table
series = {}
s_names = [a + b for a in ["indexed_toctou", "multi_variable", "double_free"] for b in ["~0", ""]]
for s_name in s_names:
    f = file(s_name + ".crash_times_data")
    d = []
    nr_timeouts = 0
    for l in f.xreadlines():
        w = l.split()
        if w[-1] == "T":
            nr_timeouts += 1
        else:
            d.append(float(w[0]))
    f.close()
    series[s_name] = (d, nr_timeouts)
def __bootstrap_quantile((d, nr_timeouts), q):
    d = d + [maxtime] * nr_timeouts
    d.sort()
    return bootstrap_quantile(d, q)
statistics = [("Mean", "rcl", lambda (d, _nr_timeouts): clt_mean(d)),
              ("$10^{th}$ percentile", None, lambda d: __bootstrap_quantile(d, .1)),
              ("Median", None, lambda d: __bootstrap_quantile(d, .5)),
              ("$90^{th}$ percentile", None, lambda d: __bootstrap_quantile(d, .9))]

print r"\begin{tabbular}{|p{2.85cm}|" + "l|" * len(statistics) + "}"
print "\\hline"
print " & " + " & ".join([x[0] for x in statistics]) + "\\\\"
for testprog in ["indexed_toctou", "multi_variable", "double_free"]:
    print "\\hline"
    print bug_names[testprog] + " & " * len(statistics) + "\\\\"
    for (series_name, series_label) in [("No enforcer", ""), ("Enforcer", "~0")]:
        s_name = testprog + series_label
        assert series.has_key(s_name)
        s = series[s_name]
        print "\\hspace{1em}%s & %s\\\\" % (series_name, " & ".join([x[2](s) for x in statistics]))
print "\\hline"
print "\\end{tabbular}"
