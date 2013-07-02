#! /usr/bin/env python

import sys
import common
import math
import random
import tarfile
import re

DESIRED_FNAMES = re.compile(r"interfering[0-9]*\.bubble")

random.seed(0)

nr_replicates = 1000

early_out = "early out"
satisfiable = "satisfiable"
unsatisfiable = "unsatisfiable"
ic_atomic_false = "ic-atomic is false"
bubble_keys = set(["compiling interfering CFG", "simplifying interfering CFG", "rederive crashing",
                   "early-out", "build ic-atomic", "simplify ic-atomic", "execute ic-atomic",
                   "cross build", "cross simplify", "cross symbolic", "sat check"])
bubble_key_to_chart_key = {"compiling interfering CFG": "sicfg",
                           "simplifying interfering CFG": "sicfg",
                           "rederive crashing": "rc",
                           "early-out": "rc",
                           "build ic-atomic": "sia",
                           "simplify ic-atomic": "sia",
                           "execute ic-atomic": "eia",
                           "cross build": "cs",
                           "cross simplify": "cs",
                           "cross symbolic": "ce",
                           "sat check": "ce"}
chart_keys = ["sicfg", "rc", "sia", "eia", "cs", "ce"]
chart_labels = {"cicfg": "Build interfering \\gls{cfg}",
                "sicfg": "Build interfering {\\StateMachine}",
                "rc": "Rederive crashing {\\StateMachine}",
                "early-out": "Early-out check",
                "bia": "Build \\gls{ic-atomic} {\\StateMachine}",
                "sia": "Build \\gls{ic-atomic} {\\StateMachine}",
                "eia": "Run \\gls{ic-atomic} {\\StateMachine}",
                "cb": "Build cross-product {\\StateMachine}",
                "cs": "Build cross-product {\\StateMachine}",
                "ce": "Run cross-product {\\StateMachine}",
                "sc": "Final satisfiability check"}
START_INTERFERING_RE = re.compile(r"start interfering CFG [0-9]*/[0-9]* for DynRip\[[0-9a-f]*\]")
def read_one_sequence(defects, get_line, _pushback, fname):
    t = get_line()
    if t == None:
        return None
    (when, msg) = t
    if not START_INTERFERING_RE.match(msg):
        common.fail("Lost sequencing at %s in %s" % (msg, fname))
    start_time = when
    expected_start = when
    r = []
    key = None
    while True:
        (when, msg) = get_line()
        if msg == "stop interfering CFG":
            end_time = when
            (_, msg) = get_line()
            w = msg.split()
            if w[:2] != ["high", "water:"]:
                common.fail("Lost sequencing 2 at %s" % msg)
            break
        w = msg.split()
        if msg in [early_out, satisfiable, unsatisfiable, ic_atomic_false]:
            r.append(msg)
            continue
        assert w[0] == "start"
        start = when
        key = " ".join(w[1:])
        assert key in bubble_keys

        if not defects.has_key(key):
            defects[key] = 0
        defects[key] += start - expected_start

        t = get_line()
        if t == None:
            return None
        (when, msg) = t
        rr = {"key": key, "duration": when - start}
        if msg == "timeout":
            rr["failed"] = "timeout"
        elif msg == "out of memory":
            rr["failed"] = "oom"
        else:
            assert msg.split()[0] == "stop" and " ".join(msg.split()[1:]) == key
            rr["failed"] = None
        expected_start = when
        r.append(rr)
        if rr["failed"]:
            end_time = when
            break
    # Check for leftovers
    t = get_line()
    assert t == None

    if not defects.has_key("leftover"):
        defects["leftover"] = 0
    defects["leftover"] += end_time - expected_start
    if key != None:
        r.append({"key": key, "duration": end_time - expected_start, "failed": None})
    return (end_time - start_time, r)

defects = {}
sequences = []
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
    r = read_one_sequence(defects, get_line, lambda _: abort(), ti.name)
    content.close()
    if r != None:
        sequences.append(r)

t.close()

print "Done parse input"

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
            if event == early_out:
                for k in ["sia", "eia", "cs", "ce"]:
                    charts[k].pre_dismissed += 1
                continue
            if event == ic_atomic_false:
                for k in ["cs", "ce"]:
                    charts[k].pre_dismissed += 1
                continue
            if event in [satisfiable, unsatisfiable]:
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

replicates = [sequences_to_chartset([random.choice(sequences) for _ in xrange(len(sequences))]) for _2 in xrange(nr_replicates)]
(charts, defect_samples, total_samples) = sequences_to_chartset(sequences)

main_fig = common.Figure(time_to_y, y_to_time, [])
main_fig.figwidth -= 0.5
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

output = file(sys.argv[1], "w")

output.write("\\begin{tikzpicture}\n")

common.draw_furniture(output, chart_keys, main_fig)
common.draw_pdfs(output, chart_keys, charts, defect_samples, total_samples, replicates, chart_labels, main_fig)

output.write("\\end{tikzpicture}\n")
output.close()
