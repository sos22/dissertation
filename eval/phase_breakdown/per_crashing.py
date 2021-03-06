#! /usr/bin/env python

import sys
import math
import random
import decimal
import common
import tarfile
import re

DESIRED_FNAMES = re.compile(r"crashing[0-9]*\.bubble")

random.seed(0)

max_cdfs = 50.0
nr_replicates = 1000

no_interfering_stores = "no interfering stores"
early_out = "early out"
plt = "Dismiss early, PLT"
bubble_keys = set(["early out", "early-out check", "build crashing CFG", "compile crashing machine", "ssa crashing machine", "simplify crashing machine", "derive c-atomic", "derive interfering CFGs", "process interfering CFGs", "GC", "misc1", "misc2", "misc3", "IO"])

chart_keys = ["build_ccfg", "compile_csm", "simplify_csm",
              "derive_icfgs", "derive_catomic", "per_icfg" ]
bubble_key_to_chart_key = {"early out": "build_ccfg",
                           "early-out check": "build_ccfg",
                           "build crashing CFG": "build_ccfg",
                           "compile crashing machine": "compile_csm",
                           "ssa crashing machine": "compile_csm",
                           "simplify crashing machine": "simplify_csm",
                           "derive c-atomic": "derive_catomic",
                           "derive interfering CFGs": "derive_icfgs",
                           "process interfering CFGs": "per_icfg",
                           "GC": "build_ccfg",
                           "misc1": "build_ccfg",
                           "misc2": "derive_icfgs",
                           "misc3": "derive_icfgs",
                           "IO": "build_ccfg"}
chart_labels = {"early_out": "Early out",
                "build_ccfg": "\\subcrash{0}",
                "compile_csm": "\\subcrash{1}",
                "ssa_csm": "SSA crashing {\\StateMachine}",
                "simplify_csm": "\\subcrash{2}",
                "derive_icfgs": "\\subcrash{3}",
                "derive_catomic": "\\subcrash{4}",
                "per_icfg": "\\subcrash{5}"}

START_CRASHING_RE = re.compile(r"start crashing thread DynRip\[[0-9a-f]*\]")

def read_one_sequence(defects, get_line, pushback, fname):
    (when, msg) = get_line()
    if not START_CRASHING_RE.match(msg):
        common.fail("Lost sequencing at %s in %s" % (msg, fname))
    start_time = when
    expected_start = when
    nr_produced = 0
    r = []
    key = None
    have_compile = False
    while True:
        (when, msg) = get_line()
        if msg == "finish crashing thread":
            end_time = when
            break
        if msg == plt:
            r.append(plt)
            continue
        if msg == "done PLT check":
            continue
        w = msg.split()
        if w[0:2] == ["high", "water:"]:
            continue
        if w[0] == "Marker1":
            continue
        assert w[0] == "start"
        start = when
        key = " ".join(w[1:])
        if key == "compile crashing machine":
            if have_compile:
                key = "ssa crashing machine"
                have_compile = None
            else:
                assert have_compile == False
                have_compile = True
        assert key in bubble_keys

        if not defects.has_key(key):
            defects[key] = 0
        defects[key] += start - expected_start

        (when, msg) = get_line()
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
                (what, msg) = get_line()
                rr["duration"] = when - start
            #assert msg.split()[0] in ["stop", "finish"] and " ".join(msg.split()[1:]) == key
            rr["failed"] = None
        expected_start = when
        r.append(rr)
        l = get_line()
        if l != None:
            if l[1] in [no_interfering_stores, early_out]:
                assert nr_produced == 0
                r.append(l[1])
            else:
                pushback("%f: %s\n" % (l[0], l[1]))
    # Check for leftovers
    t = get_line()
    assert t == None
    if not defects.has_key("leftover"):
        defects["leftover"] = 0
    defects["leftover"] += end_time - expected_start
    if key != None:
        r.append({"key": key, "duration": end_time - expected_start, "failed": None})
    return ((end_time - start_time, r), nr_produced)

defects = {}
sequences = []
nr_produced_series = []

t = tarfile.open("bubbles.tar")
while True:
    ti = t.next()
    if ti == None:
        break
    if not ti.isfile() or not DESIRED_FNAMES.match(ti.name):
        continue
    content = t.extractfile(ti)
    lines = common.pushback(iter(content))
    def get_line():
        try:
            l = lines.next()
        except StopIteration:
            return None
        w = l.split()
        assert w[0][-1] == ":"
        msg = " ".join(w[1:])
        if msg in ["exit, status 0", "parent woke up"]:
            return get_line()
        return (float(w[0][:-1]), msg)
    def pushback(l):
        lines.q.append(l)
    (sequence, nr_produced) = read_one_sequence(defects, get_line, pushback, ti.name)
    content.close()
    nr_produced_series.append(nr_produced)
    sequences.append(sequence)
nr_produced_series.sort()

t.close()

print "Done parse input"

output = file("per_crashing.tex", "w")
output.write("%% Defects by phase:\n")
tot_defect = 0
for (v, k) in sorted([(v, k) for (k, v) in defects.iteritems()]):
    output.write("%%%% \t%s -> %f\n" % (k, v))
    tot_defect += v
tot_defect -= defects["leftover"]
output.write("%%%% total: %f\n" % tot_defect)

nr_chartsets_built = 0
def sequences_to_chartset(sequences):
    global nr_chartsets_built
    print "Building chartset %d" % nr_chartsets_built
    nr_chartsets_built += 1
    
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
                for (k, v) in charts.iteritems():
                    if k != "build_ccfg":
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

# Interfering time per crashing instruction
def gen_replicate1():
    cs = random.choice(sequences)
    events = cs[1]
    res = 0.0
    cntr = 0
    for event in events:
        if event in [no_interfering_stores, early_out, plt]:
            return 0.0
        if event["failed"]:
            return None
        if event["key"] == "process interfering CFGs":
            res += event["duration"]
            cntr += 1
    return res
def gen_replicate():
    acc = 0
    cntr = 0
    while cntr < len(sequences):
        r = gen_replicate1()
        if r != None:
            acc += r
            cntr += 1
    return acc / cntr
def gen_replicates():
    return [gen_replicate() for _ in xrange(nr_replicates)]
repl = gen_replicates()
repl.sort()
print "Interfering time per crashing instruction: %f, %f %d" % (common.quantile(repl, 0.05), common.quantile(repl, 0.95), len(sequences))

replicates = [sequences_to_chartset([random.choice(sequences) for _ in xrange(len(sequences))]) for _2 in xrange(nr_replicates)]
(charts, defect_samples, total_samples) = sequences_to_chartset(sequences)

main_fig = common.Figure(time_to_y, y_to_time, [])


output.write("\\begin{tikzpicture}\n")

common.draw_furniture(output, chart_keys, main_fig)
common.draw_pdfs(output, chart_keys, charts, defect_samples, total_samples, replicates, chart_labels, main_fig)

output.write("\\end{tikzpicture}\n")
output.close()
