#! /usr/bin/env python

import sys
import random

expected_keys = ["early-out check", "build crashing CFG", "compile crashing machine", "GC",
                 "simplify crashing machine", "derive interfering CFGs", "derive c-atomic",
                 "process interfering CFGs"]
_lookahead_line = None
def get_record(inp):
    global _lookahead_line
    def get_line():
        global _lookahead_line
        if _lookahead_line != None:
            res = _lookahead_line
            _lookahead_line = None
            return res
        l = inp.readline()
        if l == "":
            return (0, None)
        l = l.strip()
        w = l.split(":")
        return (float(w[0]), w[1][1:])
    def peek_line():
        global _lookahead_line
        _lookahead_line = get_line()
        return _lookahead_line[1]

    (when, msg) = get_line()
    if msg == None:
        return None
    if msg != "start crashing thread":
        print "Lost sync at %s" % (str((when, msg)))
        sys.exit(1)
    record = {}
    for k in expected_keys:
        record[k] = { "dismiss": False,
                      "failed": False,
                      "time": 0 }
    record["nr_store_cfgs"] = None
    startT = when
    while True:
        (when, msg) = get_line()
        if msg == "finish crashing thread":
            break
        if msg == "Dismiss early, PLT":
            record["early-out check"]["dismiss"] = True
            continue
        if msg[:9] == "produced " and msg[-17:] == " interfering CFGs":
            record["nr_store_cfgs"] = int(msg[9:-17])
            continue
        assert msg[:6] == "start "
        k = msg[6:]
        assert k in expected_keys

        (end, endMsg) = get_line()
        record[k]["time"] += end - when
        if endMsg == "timeout":
            if not k in ["simplify crashing machine", "derive interfering CFGs"]:
                sys.stderr.write("Failure at %s\n" % k)
            record[k]["failed"] = True
        else:
            assert endMsg[:5] == "stop "
            assert endMsg[5:] == k
            l = peek_line()
            if l in ["early out", "no interfering stores"]:
                if not k in ["early-out check", "derive interfering CFGs"]:
                    sys.stderr.write("%s dismisses at %s\n" % (l, k))
                record[k]["dismiss"] = True
                _lookahead_line = None
    endT = when
    record["tot_time"] = endT - startT
    return record

inp = file(sys.argv[1])
series = []
while True:
    s = get_record(inp)
    if s == None:
        break
    series.append(s)
inp.close()

print "%d samples" % len(series)

def count_stat(name, count, base):
    p = float(count) / base
    print "%s: $%d \pm_b %f$" % (name, count, (base * p * (1 - p)) ** .5)
def time_stat(name, samples):
    mu = sum(samples) / float(len(samples))
    sd = (sum([(x - mu) ** 2 for x in samples]) / (len(samples) * (len(samples) - 1))) ** .5
    print "%s: $%f \pm_\mu %f$" % (name, mu, sd)

nr_early_out = 0
for s in series:
    if s["early-out check"]["dismiss"]:
        nr_early_out += 1
count_stat("Nr early out", nr_early_out, len(series))

nr_early_timeout = 0
for s in series:
    if s["simplify crashing machine"]["failed"] or s["derive interfering CFGs"]["failed"]:
        nr_early_timeout += 1
count_stat("Nr early timeout", nr_early_timeout, len(series) - nr_early_out)

time_samples = []
for s in series:
    if s["early-out check"]["dismiss"] or s["simplify crashing machine"]["failed"] or s["derive interfering CFGs"]["failed"]:
        continue
    time_samples.append(s["build crashing CFG"]["time"] +
                        s["compile crashing machine"]["time"] +
                        s["GC"]["time"] +
                        s["simplify crashing machine"]["time"])
time_stat("build crashing machine", time_samples)

nr_no_interfering = 0
nr_avail = 0
for s in series:
    if s["early-out check"]["dismiss"] or s["simplify crashing machine"]["failed"] or s["derive interfering CFGs"]["failed"]:
        continue
    nr_avail += 1
    if s["derive interfering CFGs"]["dismiss"] or s["simplify crashing machine"]["dismiss"]:
        nr_no_interfering += 1
count_stat("no interfering", nr_no_interfering, nr_avail)

time_samples = []
for s in series:
    if s["early-out check"]["dismiss"] or s["simplify crashing machine"]["failed"] or s["derive interfering CFGs"]["failed"] or s["simplify crashing machine"]["dismiss"]:
        continue
    time_samples.append(s["derive interfering CFGs"]["time"])
time_stat("build interfering CFGs", time_samples)

time_samples = []
for s in series:
    if s["early-out check"]["dismiss"] or s["simplify crashing machine"]["failed"] or s["derive interfering CFGs"]["dismiss"] or s["derive interfering CFGs"]["failed"] or s["simplify crashing machine"]["dismiss"]:
        continue
    assert s["nr_store_cfgs"] != None
    time_samples.append(s["nr_store_cfgs"])
time_stat("interfering CFGs per crashing CFG", time_samples)

# Okay, and now do a bootstrap to get error bars on the total number
# of interfering CFGs.
avail = [s["nr_store_cfgs"] for s in series]
def gen_sample():
    acc = 0
    count = 0
    for i in xrange(len(avail)):
        s = avail[random.randint(0,len(avail)-1)]
        if s != None:
            acc += s
            count += 1
    return acc
a = [a for a in avail if a != None]
true_mean = sum(a)
samples = []
for i in xrange(10000):
    samples.append(gen_sample())
m = sum(samples) / len(samples)
sd = (sum([(x - m) ** 2 for x in samples]) / (len(samples) - 1)) ** .5
print "S: $%f \pm_{%d} %f$ (should be %f)" % (m, len(samples), sd, true_mean)
