#! /usr/bin/env python

# Calculate some summary statistics from a collection of bubble logs.
# Stats generated:
#
# -- Time to process each crashing instruction
# -- VCs per crashing instruction
# -- Time per crashing instr excl. per-interfering work.
# -- Proportion of failures in per-crashing phase
# -- Interfering CFGs per crashing instruction
# -- Time per interfering CFG
# -- Proportion of failures in per-interfering phase
# -- Proportion of interfering CFGs which generate verification conditions
# 

import sys
import tarfile
import re
import cPickle
import random

nr_replicates = 1000

CRASHING_FNAME = re.compile(r"crashing[0-9]*\.bubble")
START_CRASHING = re.compile(r"([0-9]*\.[0-9]*): start crashing thread (DynRip\[[0-9a-f]*\])")
START_INTERFERING = re.compile(r"([0-9]*\.[0-9]*): start interfering CFG ([0-9]*)/([0-9]*) for (DynRip\[[0-9a-f]*\])")
ORDINARY_LINE = re.compile(r"([0-9]*\.[0-9]*): (.*)")

def quantile(samples, q):
    assert 0 <= q <= 1
    idx = len(samples) * q
    idx0 = int(idx)
    idx1 = idx0 + 1
    idx = idx - idx0
    if idx1 == len(samples):
        return samples[-1]
    else:
        return samples[idx0] + (samples[idx1] - samples[idx0]) * idx

def tarfile_files(tf):
    while True:
        ti = tf.next()
        if ti == None:
            raise StopIteration
        if not ti.isfile():
            continue
        yield (ti, tf.extractfile(ti))

def load_bubblelog(filename):
    crashing = []
    interfering = []
    with tarfile.open(filename) as t:
        for (tf, content) in tarfile_files(t):
            if CRASHING_FNAME.match(tf.name):
                lines = iter(content)
                fl = next(lines)
                m = START_CRASHING.match(fl.strip())
                end_time = start_time  = float(m.group(1))
                key = m.group(2)
                failed = False
                switch_mode = None
                percrashing = None
                for l in lines:
                    m = ORDINARY_LINE.match(l.strip())
                    end_time = float(m.group(1))
                    if m.group(2) == "timeout":
                        print "Timeout"
                        failed = True
                    elif m.group(2) == "out of memory":
                        print "OOM"
                        failed = True
                    elif m.group(2) == "start process interfering CFGs":
                        percrashing = end_time - start_time
                crashing.append({"failed": failed,
                                 "tot_time": end_time - start_time,
                                 "percrashing": percrashing or end_time - start_time})
            else:
                lines = iter(content)
                try:
                    fl = next(lines)
                except StopIteration:
                    continue
                m = START_INTERFERING.match(fl.strip())
                end_time = start_time = float(m.group(1))
                idx = int(m.group(2))
                max_idx = int(m.group(3))
                assert idx < max_idx
                key = m.group(4)
                failed = False
                sat = None
                for l in lines:
                    m = ORDINARY_LINE.match(l.strip())
                    end_time = float(m.group(1))
                    if m.group(2) == "timeout":
                        failed = True
                    elif m.group(2) == "out of memory":
                        failed = True
                    elif m.group(2) == "satisfiable":
                        sat = True
                    elif m.group(2) in ["unsatisfiable", "early out", "ic-atomic is false"]:
                        sat = False
                if sat == None and failed == False:
                    print "BADGERS %s" % tf.name
                interfering.append({"failed": failed,
                                    "time": end_time - start_time,
                                    "sat": sat})
    return (crashing, interfering)

try:
    with open(sys.argv[2]) as f:
        bubbles = cPickle.load(f)
except:
    bubbles = load_bubblelog(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        cPickle.dump(bubbles, f)

def calc_stats(bubbles):
    (crashing, interfering) = bubbles

    nr_crashing = len(crashing)
    nr_interfering = len(interfering)

    time_per_crashing = 0.0
    time_per_crashing1 = 0.0
    interfering_per_crashing = 0
    fails_per_crashing = 0
    vcs = 0
    fails_per_interfering = 0
    time_per_interfering = 0.0

    for k in crashing:
        if k["failed"]:
            fails_per_crashing += 1
            continue
        time_per_crashing += k["tot_time"]
        time_per_crashing1 += k["percrashing"]

    for i in interfering:
        if i["failed"]:
            fails_per_interfering += 1
            continue
        if i["sat"]:
            vcs += 1
        time_per_interfering += i["time"]
    nc = float(nr_crashing - fails_per_crashing)
    ni = float(nr_interfering - fails_per_interfering)
    return {"time_per_instr": time_per_crashing / nc,
            "time_per_crashing": time_per_crashing1 / nc,
            "interfering_per_crashing": len(interfering) / nc,
            "fails_per_crashing": fails_per_crashing / float(nr_crashing),
            "vcs_per_crashing": vcs / nc,
            "time_per_interfering": time_per_interfering / ni,
            "fails_per_interfering": fails_per_interfering / float(nr_interfering),
            "vcs_per_interfering": vcs / ni}

def gen_replicates((crashing, interfering), nr_replicates):
    base = calc_stats((crashing, interfering))
    reps = {}
    for _ in xrange(nr_replicates):
        s = calc_stats(([random.choice(crashing) for _ in crashing],
                        [random.choice(interfering) for _ in interfering]))
        for (k, v) in s.iteritems():
            reps.setdefault(k, []).append(v)
    res = {}
    for (k, v) in reps.iteritems():
        v.sort()
        res[k] = "$%f \\in [%f, %f]_{%d}^{blah}$" % (base[k],
                                                     quantile(v, 0.05),
                                                     quantile(v, 0.95),
                                                     nr_replicates)
    return res


print "%d crashing, %d interfering" % (len(bubbles[0]), len(bubbles[1]))
g = gen_replicates(bubbles, nr_replicates)
for (k, v) in g.iteritems():
    print"%s\t%s" % (k, v)

