#! /usr/bin/env python

import sys

expected_keys = ["compiling interfering CFG", "simplifying interfering CFG", "rederive crashing",
                 "early-out", "build ic-atomic", "simplify ic-atomic", "execute ic-atomic",
                 "cross build", "cross simplify", "cross symbolic", "sat check"]

def fail(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)

_lookahead_line = None

def get_line(inp):
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
def peek_line(inp):
    global _lookahead_line
    _lookahead_line = get_line()
    return _lookahead_line[1]

def get_crashing(inp):
    (when, msg) = get_line(inp)
    if msg == None:
        return None
    w = msg.split()
    if w[0] != "start" or w[1] != "crashing":
        fail("Lost sync at %s" % str((when, msg)))
    l = []
    while True:
        (when, msg) = get_line(inp)
        w = msg.split()
        if w[0] == "stop" and w[1] == "crashing":
            break
        if msg != "start interfering CFG":
            fail("Lost sync at %s" % str((when, msg)))
        sstime = when
        intf_record = {}
        for e in expected_keys:
            intf_record[e] = {"failed": None, "dismiss": False, "time": 0}
        intf_record["satisfiable"] = False
        while True:
            (when, msg) = get_line(inp)
            if msg == "stop interfering CFG":
                break
            if msg == "early out" and k == "early-out":
                intf_record["early-out"]["dismiss"] = True
                continue
            if msg == "unsatisfiable" and k == "sat check":
                intf_record["satisfiable"] = False
                continue
            if msg == "satisfiable" and k == "sat check":
                intf_record["satisfiable"] = True
                continue
            if msg == "ic-atomic is false" and k == "execute ic-atomic":
                intf_record["execute ic-atomic"]["dismiss"] = True
                continue
            assert msg[:6] == "start "
            k = msg[6:]
            assert k in expected_keys

            (end, endMsg) = get_line(inp)
            intf_record[k]["time"] += end - when

            if endMsg == "out of memory":
                intf_record[k]["failed"] = "oom"
                break
            elif endMsg == "timeout":
                intf_record[k]["failed"] = "timeout"
                break
            else:
                assert endMsg[:5] == "stop "
                assert endMsg[5:] == k

        l.append((when - sstime, intf_record))
    return l

inp = file(sys.argv[1])
series = []
while True:
    s = get_crashing(inp)
    if s == None:
        break
    series.append(s)
inp.close()

time_samples = []
nr_oom = 0
nr_timeout = 0
for s in series:
    for l in s:
        oom = False
        timeout = False
        for x in l[1].itervalues():
            if x == False or x == True:
                continue
            if x["failed"] == "oom":
                oom = True
            elif x["failed"] == "timeout":
                timeout = True
            else:
                assert x["failed"] == None
        assert not (oom and timeout)
        if oom:
            nr_oom += 1
        elif timeout:
            nr_timeout += 1
        else:
            time_samples.append(l[0])

mean = sum(time_samples) / len(time_samples)
sd = (sum([(x - mean) ** 2 for x in time_samples]) / (len(time_samples) * (len(time_samples) - 1))) ** .5
print "Time taken: %f pm %f" % (mean, sd)

def stat(nr, count):
    p = float(nr) / count
    sd = (count * p * (1 - p)) ** .5
    return "%f \pm %f" % (p * 100, sd / count * 100)
print "nr_timeout %d, nr_oom %d, len(time_samples) %d" % (nr_timeout, nr_oom, len(time_samples))
print "timeout: %s" % stat(nr_timeout, len(time_samples) + nr_timeout + nr_oom)
print "oom: %s" % stat(nr_oom, len(time_samples) + nr_timeout + nr_oom)


nr_non_failed = 0
nr_sat = 0
for s in series:
    for l in s:
        failed = False
        for x in l[1].itervalues():
            if x == False or x == True:
                continue
            if x["failed"] != None:
                failed = True
                break
        if not failed:
            nr_non_failed += 1
            if l[1]["satisfiable"]:
                nr_sat += 1
print "Generatingn VCs: %s" % stat(nr_sat, nr_non_failed)

