#! /usr/bin/env python

import common
import math
import random

import math
import random
import decimal
import common

random.seed(0)

max_cdfs = 50.0
nr_replicates = 10

bubble_keys = set(["canonicalise", "prepare summary", "slice by hb", "determine input availability",
                   "happensBeforeMapT() constructor", "place side conditions", "simplify plan",
                   "build strategy", "compile", "gcc"])

chart_keys = ["slice by hb",
              "determine input availability",
              "place side conditions",
              "build strategy",
              "compile" ]
bubble_key_to_chart_key = {}
chart_labels = {}
for k in bubble_keys:
    bubble_key_to_chart_key[k] = k
    chart_labels[k] = k
bubble_key_to_chart_key["canonicalise"] = "slice by hb"
bubble_key_to_chart_key["prepare summary"] = "slice by hb"
bubble_key_to_chart_key["happensBeforeMapT() constructor"] = "place side conditions"
bubble_key_to_chart_key["simplify plan"] = "place side conditions"
bubble_key_to_chart_key["gcc"] = "compile"

chart_labels["slice by hb"] = "Extract happens-before graph"
chart_labels["determine input availability"] = "Determine input availability"
chart_labels["place side conditions"] = "Place side conditions"
chart_labels["build strategy"] = "Build patch strategy"
chart_labels["compile"] = "Compile"

def read_one_sequence(defects):
    try:
        (when, msg) = common.get_line()
    except StopIteration:
        return None
    w = msg.split()
    if w[:-1] != ["start", "build", "enforcer"]:
        common.fail("Lost sequencing at %s" % msg)
    start_time = when
    expected_start = when
    nr_produced = 0
    r = []
    key = None
    while True:
        (when, msg) = common.get_line()
        if msg == "stop build enforcer":
            end_time = when
            if key != None:
                r.append({"key": key, "duration": end_time - expected_start, "failed": None})
            break
        w = msg.split()
        assert w[0] == "start"
        start = when
        key = " ".join(w[1:])
        assert key in bubble_keys

        if not defects.has_key(key):
            defects[key] = 0
        assert start >= expected_start
        defects[key] += start - expected_start

        (when, msg) = common.get_line()
        assert when > start
        rr = {"key": key, "duration": when - start}
        r.append(rr)
        if msg == "timeout":
            rr["failed"] = "timeout"
            end_time = when
            break
        elif msg == "out of memory":
            rr["failed"] = "oom"
            end_time = when
            break
        else:
            w = msg.split()
            assert msg.split()[0] == "stop" and " ".join(msg.split()[1:]) == key
            rr["failed"] = None
        expected_start = when
    if not defects.has_key("leftover"):
        defects["leftover"] = 0
    assert end_time > expected_start
    defects["leftover"] += end_time - expected_start
    return ((end_time - start_time, r), nr_produced)

defects = {}
sequences = []
nr_produced_series = []
cntr = 0
while True:
    r = read_one_sequence(defects)
    if r == None:
        break
    (sequence, nr_produced) = r
    nr_produced_series.append(nr_produced)
    sequences.append(sequence)
nr_produced_series.sort()

output = file("build_enforcer.tex", "w")
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
            assert event["duration"] > 0
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
                    if chart_key == "build strategy" and sample < 0.0001:
                        charts["build strategy"].pre_dismissed += 1
                        charts["compile"].pre_dismissed += 1
                    else:
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
        if defect < 0:
            print "total %f, events %s, defect %f" % (total, str(events), defect)
        assert defect >= 0
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
main_fig.nr_time_steps = 100.0
main_fig.kernel_box_height = 1.0
main_fig.figwidth -= 0.3
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

common.draw_furniture(output, chart_keys, main_fig)
common.draw_pdfs(output, chart_keys, charts, defect_samples, total_samples, replicates, chart_labels, main_fig)

output.write("\\end{tikzpicture}\n")
output.close()
