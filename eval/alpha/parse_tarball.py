#! /usr/bin/env python

# This just takes one of the bubble tarballs and turns it into a more
# easily-parsed pickle structure.

# This we need to extract:
#
# -- Total time per crashing instruction
# -- Number of timeouts in per-crashing phase
# -- Number of OOMs in per-crashing phase
# -- Number of interfering CFGs generated
# -- Number of timeouts in per-interfering phase
# -- Number of OOMs in per-interfering phase
# -- Number of VCs generated
#
# And we need to track with and without rerun information separately.
#
# Output is structured like so:
#
# RIP -> Crashing # Map from crashing instruction address to Crashing structure
# Crashing =
#   (Float,                # Time taken in seconds, excl. interfering phase
#    Float,                # Time taken in seconds, incl. interfering phase
#    ("timeout" +          # If it timed out
#     ("oom", Crashing) +  # If it OOMed and re-ran
#     Int -> Interfering)  # If it succeeded
# Interfering =
#   (Float,                # Time taken, in seconds
#    "timeout" + ("oom", Interfering) + "satisfiable" + "unsatisfiable")

import cPickle
import sys
import tarfile
import re

BASE_CRASHING_RE = re.compile(r"[0-9]*/crashing[0-9]*\.bubble$")
OLD_CRASHING_RE = re.compile(r"[0-9]*/backup[0-9]*/crashing[0-9]*\.bubble$")
BASE_INTERFERING_RE = re.compile(r"[0-9]*/interfering[0-9]*\.bubble$")
OLD_INTERFERING_RE = re.compile(r"[0-9]*/interfering[0-9]*\.bubble\.bak$")
DUMMY_INTERFERING_RE = re.compile(r"[0-9]*/backup[0-9]*/interfering[0-9]*\.bubble(\.bak)?$")
CRASHING_SUB_RERUN_RE = re.compile(r"[0-9]*/interfering\.DynRip\[[0-9a-f]*\]\.[0-9]*\.bubble$")

FIRST_CRASHING_LINE_RE = re.compile(r"([0-9]*\.[0-9]*): start crashing thread (DynRip\[[0-9a-f]*\])")
FIRST_INTERFERING_LINE_RE = re.compile(r"([0-9]*\.[0-9]*): start interfering CFG ([0-9]*)/[0-9]* for (DynRip\[[0-9a-f]*\])")
ORDINARY_LINE_RE = re.compile(r"([0-9]*\.[0-9]*): (.*)")

def load_crashing_log(fname, content, output):
    lines = iter(content)
    first = next(lines).strip()
    m = FIRST_CRASHING_LINE_RE.match(first)
    assert m
    start_time = float(m.group(1))
    rip = m.group(2)

    assert not output.has_key(rip)

    timeout = False
    oom = False
    end_time = start_time
    switch_time = end_time
    switched = False
    for line in lines:
        m = ORDINARY_LINE_RE.match(line.strip())
        end_time = float(m.group(1))
        if not switched:
            switch_time = end_time
        if m.group(2) == "timeout":
            timeout = True
            break
        elif m.group(2) == "out of memory":
            oom = True
            break
        elif m.group(2) == "start process interfering CFGs":
            switched = True
    if timeout:
        r = "timeout"
    elif oom:
        r = ("oom", None)
    else:
        r = {}
    r = (switch_time - start_time, end_time - start_time, r)
    output[rip] = r

def load_interfering_log(fname, content, output):
    lines = iter(content)
    try:
        first = next(lines).strip()
    except StopIteration:
        return
    m = FIRST_INTERFERING_LINE_RE.match(first)
    start_time = float(m.group(1))
    key = (m.group(3), int(m.group(2)))

    assert not output.has_key(key)

    timeout = False
    oom = False
    satisfiable = False
    end_time = start_time
    for line in lines:
        m = ORDINARY_LINE_RE.match(line.strip())
        end_time = float(m.group(1))
        if m.group(2) == "timeout":
            timeout = True
            break
        elif m.group(2) == "out of memory":
            oom = True
            break
        elif m.group(2) == "satisfiable":
            satisfiable = True
            break
    if timeout:
        r = "timeout"
    elif oom:
        r = ("oom", None)
    elif satisfiable:
        r = "satisfiable"
    else:
        r = "unsatisfiable"
    r = (end_time - start_time, r)
    output[key] = r

crashing = {}
interfering = {}
crashing_i_rerun = {}
interfering_pre_rerun = {}
crashing_pre_rerun = {}

t = tarfile.open(sys.argv[1])
while True:
    ti = t.next()
    if ti == None:
        break
    if not ti.isfile():
        continue
    content = t.extractfile(ti)
    if BASE_CRASHING_RE.match(ti.name):
        load_crashing_log(ti.name, content, crashing)
    elif OLD_CRASHING_RE.match(ti.name):
        load_crashing_log(ti.name, content, crashing_pre_rerun)
    elif BASE_INTERFERING_RE.match(ti.name):
        load_interfering_log(ti.name, content, interfering)
    elif CRASHING_SUB_RERUN_RE.match(ti.name):
        load_interfering_log(ti.name, content, crashing_i_rerun)
    elif OLD_INTERFERING_RE.match(ti.name):
        load_interfering_log(ti.name, content, interfering_pre_rerun)
    elif DUMMY_INTERFERING_RE.match(ti.name):
        pass
    else:
        sys.stderr.write("Unrecognised file name .%s.\n" % repr(ti.name))
        sys.exit(1)

# Now assemble those into an output file.
output = {}

# First, attach interfering logs generated while re-running crashing
# threads to the relevant crashing log.
for ((rip, idx), v) in crashing_i_rerun.iteritems():
    assert crashing.has_key(rip)
    c = crashing[rip]
    if c[2] == ("oom", None):
        continue
    assert not c[2].has_key(idx)
    c[2][idx] = v

# Now attach the initial interfering runs
for ((rip, idx), v) in interfering.iteritems():
    assert crashing.has_key(rip)
    c = crashing[rip]
    assert not c[2].has_key(idx)
    c[2][idx] = v
# And the old interfering runs
for ((rip, idx), v) in interfering_pre_rerun.iteritems():
    assert crashing.has_key(rip)
    c = crashing[rip]
    assert v[1] == ("oom", None)
    c[2][idx] = (v[0], ("oom", c[2][idx]))

# Add in re-runs of crashing threads.
for (k, v) in crashing_pre_rerun.iteritems():
    assert v[2] == ("oom", None)
    crashing[k] = (v[0], v[1], ("oom", crashing[k]))

with open(sys.argv[2], "w") as f:
    cPickle.dump(crashing, f)

sys.exit(0)

# Dump it out.
for (k, v) in crashing.iteritems():
    print "%s: %f %f" % (k, v[0], v[1]),
    if v[2] == "timeout":
        print " timeout"
    elif isinstance(v[2], tuple):
        assert v[2][0] == "oom"
        print " OOM, rerun"
        r = v[2][1]
        assert r != None
        print "\t%f %f" % (r[0], r[1]),
        if r[2] == "timeout":
            print "timeout"
        elif isinstance(r[2], tuple):
            assert r[2] == ("oom", None)
            print "oom"
        else:
            print
            for (ki, vi) in r[2].iteritems():
                print "\t\t%d -> %f" % (ki, vi[0]),
                if isinstance(vi[1], str):
                    print " %s" % vi[1]
                else:
                    assert vi[1] == ("oom", None)
                    print " OOM"
    else:
        print
        for (ki, vi) in v[1].iteritems():
            print "\t%d -> %f" % (ki, vi[0]),
            if isinstance(vi[1], str):
                print " %s" % vi[1]
            else:
                assert vi[1][0] == "oom"
                print " OOM, rerun"
                r = vi[1][1]
                print "\t\t%f " % r[0],
                if isinstance(r[1], str):
                    print "%s" % r[1]
                else:
                    assert r[1] == ("oom", None)
                    print "OOM"
                
            

