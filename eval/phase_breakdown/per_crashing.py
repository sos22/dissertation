#! /usr/bin/env python

import sys
import math
import random
import decimal
import common

random.seed(0)

max_cdfs = 50.0
nr_replicates = 1000

no_interfering_stores = "no interfering stores"
early_out = "early out"
plt = "Dismiss early, PLT"
bubble_keys = set(["early out", "early-out check", "build crashing CFG", "compile crashing machine", "simplify crashing machine", "derive c-atomic", "derive interfering CFGs", "process interfering CFGs", "GC", "misc1", "misc2", "misc3", "IO"])

chart_keys = ["build_ccfg", "compile_csm", "simplify_csm",
              "derive_icfgs", "derive_catomic", "per_icfg" ]
bubble_key_to_chart_key = {"early out": "build_ccfg",
                           "early-out check": "build_ccfg",
                           "build crashing CFG": "build_ccfg",
                           "compile crashing machine": "compile_csm",
                           "simplify crashing machine": "simplify_csm",
                           "derive c-atomic": "derive_catomic",
                           "derive interfering CFGs": "derive_icfgs",
                           "process interfering CFGs": "per_icfg",
                           "GC": "build_ccfg",
                           "misc1": "build_ccfg",
                           "misc2": "derive_icfgs",
                           "misc3": "derive_icfgs",
                           "IO": "build_ccfg"}
chart_labels = {"build_ccfg": "Build crashing \\gls{cfg}",
                "compile_csm": "Compile crashing {\\StateMachine}",
                "simplify_csm": "Simplify crashing {\\StateMachine}",
                "derive_icfgs": "Derive interfering \\glspl{cfg}",
                "derive_catomic": "Derive C-atomic",
                "per_icfg": "Process interfering \\glspl{cfg}"}
def read_one_sequence(defects):
    try:
        (when, msg) = common.get_line()
    except StopIteration:
        return None
    if msg != "start crashing thread":
        common.fail("Lost sequencing at %s" % msg)
    start_time = when
    expected_start = when
    nr_produced = 0
    r = []
    key = None
    while True:
        (when, msg) = common.get_line()
        if msg == "finish crashing thread":
            end_time = when
            break
        if msg == plt:
            r.append(plt)
            continue
        if msg in ["done PLT check", "parent woke up"]:
            continue
        w = msg.split()
        if w[0:2] == ["high", "water:"]:
            continue
        if w[0] == "Marker1":
            continue
        assert w[0] == "start"
        start = when
        key = " ".join(w[1:])
        assert key in bubble_keys

        if not defects.has_key(key):
            defects[key] = 0
        defects[key] += start - expected_start

        (when, msg) = common.get_line()
        rr = {"key": key, "duration": when - start}
        if msg == "timeout":
            rr["failed"] = "timeout"
        elif msg == "out of memory":
            rr["failed"] = "oom"
        else:
            w = msg.split()
            if w[0] == "produced" and w[2] == "interfering" and w[3] == "CFGs":
                assert nr_produced == 0
                nr_produced = int(w[1])
                (what, msg) = common.get_line()
                rr["duration"] = when - start
            assert msg.split()[0] in ["stop", "finish"] and " ".join(msg.split()[1:]) == key
            rr["failed"] = None
        expected_start = when
        r.append(rr)
        l = next(common.stdin)
        lookahead = " ".join(l.split()[1:])
        if lookahead in [no_interfering_stores, early_out]:
            assert nr_produced == 0
            r.append(lookahead)
        else:
            common.stdin.q.append(l)
    if not defects.has_key("leftover"):
        defects["leftover"] = 0
    defects["leftover"] += end_time - expected_start
    if key != None:
        r.append({"key": key, "duration": end_time - expected_start, "failed": None})
    return ((end_time - start_time, r), nr_produced)

defects = {}
sequences = []
nr_produced_series = []
while True:
    r = read_one_sequence(defects)
    if r == None:
        break
    (sequence, nr_produced) = r
    nr_produced_series.append(nr_produced)
    sequences.append(sequence)
nr_produced_series.sort()

output = file("per_crashing.tex", "w")
output.write("%% Defects by phase:\n")
tot_defect = 0
for (v, k) in sorted([(v, k) for (k, v) in defects.iteritems()]):
    output.write("%%%% \t%s -> %f\n" % (k, v))
    tot_defect += v
tot_defect -= defects["leftover"]
output.write("%%%% total: %f\n" % tot_defect)

def sequences_to_chartset(sequences):
    charts = {}
    for k in chart_keys:
        charts[k] = common.Chart()
    defect_samples = []
    total_samples = []
    cntr = 0
    for (total, events) in sequences:
        defect = total
        samples = {}
        failed_at = {}
        for event in events:
            if event == no_interfering_stores:
                charts["per_icfg"].pre_dismissed += 1
                charts["derive_catomic"].pre_dismissed += 1
                continue
            if event in [early_out, plt]:
                for v in charts.itervalues():
                    v.pre_dismissed += 1
                continue
            f = event["failed"]
            k = bubble_key_to_chart_key[event["key"]]
            if f != None:
                assert not failed_at.has_key(k)
                assert k != None
                failed_at[k] = f
                defect -= event["duration"]
                need_exit = True
            elif k != None:
                samples[k] = samples.get(k,0) + event["duration"]
        for (chart_key, sample) in samples.iteritems():
            if chart_key != None:
                defect -= sample
                if not chart_key in failed_at:
                    charts[chart_key].samples.append(sample)
        if len(failed_at) != 0:
            assert len(failed_at) == 1
            chart_key = next(iter(failed_at))
            if failed_at[chart_key] == "timeout":
                charts[chart_key].timeouts += 1
            else:
                charts[chart_key].ooms += 1
        else:
            total_samples.append(total)
        cntr += 1
        defect_samples.append(defect)
    print "%d/%d" % (len(total_samples), cntr)
    acc = 0
    for ck in chart_keys:
        charts[ck].pre_failed = acc
        acc += charts[ck].timeouts + charts[ck].ooms
        charts[ck].samples.sort()
    defect_samples.sort()
    total_samples.sort()
    return (charts, defect_samples, total_samples)

def time_to_y(t):
    return math.log(t / main_fig.mintime) / math.log(main_fig.maxtime / main_fig.mintime) * (main_fig.y_max - main_fig.y_min) + main_fig.y_min
def y_to_time(y):
    return math.e ** ((y - main_fig.y_min) / (main_fig.y_max - main_fig.y_min) * math.log(main_fig.maxtime / main_fig.mintime)) * main_fig.mintime

replicates = [sequences_to_chartset([random.choice(sequences) for _ in xrange(len(sequences))]) for _2 in xrange(nr_replicates)]
(charts, defect_samples, total_samples) = sequences_to_chartset(sequences)

main_fig = common.Figure(time_to_y, y_to_time, [])
main_fig.boxes.append(common.Box(main_fig.lowest() - 0.5,
                                 main_fig.lowest(),
                                 lambda x: x.pre_dismissed,
                                 lambda x: x.pre_failed,
                                 "Skipped"))
main_fig.boxes.append(common.Box(main_fig.highest(),
                                 main_fig.highest() + 0.5,
                                 lambda x: x.timeouts,
                                 lambda x: x.ooms,
                                 "Failed"))


output.write("\\begin{tikzpicture}\n")

common.draw_furniture(output, main_fig)
common.draw_pdfs(output, chart_keys, charts, defect_samples, total_samples, replicates, chart_labels, main_fig)

output.write("\\end{tikzpicture}\n")
output.close()

n = float(len(nr_produced_series))
nr_zero = float(len(filter(lambda x: x == 0, nr_produced_series)))
base_prob = .6
def count_to_x(count):
    return count * main_fig.figwidth / max_cdfs
def prob_to_y(prob):
    prob -= base_prob
    return prob * (main_fig.y_max - main_fig.y_min) + main_fig.y_min

def draw_field(output, xscale, yscale, xmarks, ymarks):
    maxx = max(map(xscale, xmarks))
    minx = min(map(xscale, xmarks))
    maxy = max(map(yscale, ymarks))
    miny = min(map(yscale, ymarks))
    # Axes and field.
    for xlabel in xmarks:
        output.write("  \\draw [color=black!10] (%f, %f) -- (%f, %f);\n" % (xscale(xlabel), miny,
                                                                            xscale(xlabel), maxy))
        output.write("  \\node at (%f, %f) [below] {%s};\n" % (xscale(xlabel), miny, xlabel))
    for ylabel in ymarks:
        if ylabel >= base_prob * 100:
            output.write("  \\draw [color=black!10] (%f, %f) -- (%f, %f);\n" % (minx, yscale(ylabel), maxx, yscale(ylabel)))
            output.write("  \\node at (%f, %f) [left] {%s};\n" % (minx, yscale(ylabel), ylabel))
    output.write("  \\draw[->] (%f, %f) -- (%f, %f);\n" % (minx, miny, maxx, miny))
    output.write("  \\draw[->] (%f, %f) -- (%f, %f);\n" % (minx, miny, minx, maxy))

# Do a CDF of the number of interfering CFGs generated per instruction.
output = file("nr_produced_cdf.tex", "w")
output.write("\\begin{tikzpicture}\n")
draw_field(output, lambda x: count_to_x(float(x)), lambda perc: prob_to_y(float(perc[:-2])/100.0), map(str, xrange(0,int(max_cdfs)+1,10)), ["%d\\%%" % x for x in xrange(int(100*base_prob),101,5)])

# Data series
dkw_bound = (-math.log(0.9/2) / (2 * n)) ** .5
print "dkw_bound %f (%d samples)" % (dkw_bound, len(nr_produced_series))
for level in xrange(1, int(max_cdfs)+1):
    cum = float(len(filter(lambda x: x < level, nr_produced_series))) / len(nr_produced_series)
    low = cum - dkw_bound
    high = cum + dkw_bound
    if high > 1:
        high = 1
    output.write("  \\fill [color=black!50] (%f, %f) rectangle (%f, %f);\n" % (count_to_x(level - .5), prob_to_y(low),
                                                                               count_to_x(level + .5), prob_to_y(high)))
    output.write("  \\draw (%f, %f) -- (%f, %f);\n" % (count_to_x(level - .5), prob_to_y(cum),
                                                       count_to_x(level + .5), prob_to_y(cum)))

output.write("\\end{tikzpicture}\n")
output.close()

# Now do a count table
cums = []
acc = 0
for s in nr_produced_series:
    acc += s
    cums.append(s)
cums.sort(reverse = True)
def x_scale(nr_crashing):
    return nr_crashing * main_fig.figwidth
def y_scale(nr_interfering):
    return nr_interfering * (main_fig.y_max - main_fig.y_min) + main_fig.y_min

output = file("nr_produced_counts.tex", "w")
output.write("\\begin{tikzpicture}\n")
draw_field(output, lambda x: x_scale(float(x[:-2]) / 35.0), lambda y: y_scale(float(y[:-2]) / 100), ["%d\\%%" % x for x in xrange(0,36,5)], ["%d\\%%" %x for x in xrange(0,101,10)])
output.write("  \\draw ")
first = True
for (nr_crashing, nr_interfering) in enumerate(cums):
    if nr_crashing / float(len(cums)) > .35:
        break
    if not first:
        output.write("        -- ")
    first = False
    output.write("(%f, %f)\n" % (x_scale(nr_crashing / float(len(cums))), y_scale(nr_interfering / float(cums[0]))))
output.write("        ;\n")
output.write("\\end{tikzpicture}\n")
