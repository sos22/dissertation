#! /usr/bin/env python

import sys

def fail(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)

samples = []
while True:
    l = sys.stdin.readline().strip()
    if l == "":
        break
    w = l.split()
    t = float(w[0][:-1])
    if w[1] != "start":
        fail("lost sync at %s" % l)
    start = t
    name = w[2]

    def simple(name):
        l = sys.stdin.readline().strip()
        w = l.split()
        t = float(w[0][:-1])
        assert w[1] == "start"
        assert w[2:] == name

        l = sys.stdin.readline().strip()
        w = l.split()
        t2 = float(w[0][:-1])
        assert w[1] == "stop"
        assert w[2:] == name
        return t2 - t
    ics = simple(["identify", "critical", "sections"])

    l = sys.stdin.readline().strip()
    w = l.split()
    t = float(w[0][:-1])
    assert w[1] == "protect" and w[3] == "instructions"
    nr_instrs = int(w[2])

    bs = simple(["build", "stratgy"])
    r = simple(["recompile"])

    l = sys.stdin.readline().strip()
    w = l.split()
    t = float(w[0][:-1])
    assert w[2] == "patch" and w[3] == "points," and w[5] == "clobbered," and w[7] == "late" and w[8] == "relocations," and w[10] == "instrs," and w[12] == "bytes," and w[14] == "locks," and w[16] == "unlocks"
    nr_points = int(w[1])
    clobbered = int(w[4])
    relocs = float(w[6])
    patch_instrs = int(w[9])
    bytes = int(w[11])
    locks = int(w[13])
    unlocks = int(w[15])

    sc = simple(["system", "compile"])

    l = sys.stdin.readline().strip()
    w = l.split()
    t = float(w[0][:-1])
    assert w[1] == "stop"
    end = t

    samples.append({"name": name,
                    "tot": end - start,
                    "nr_instrs": nr_instrs,
                    "ics": ics,
                    "bs": bs,
                    "sc": sc,
                    "r": r,
                    "defect": end - start - ics - bs - sc - r,
                    "np": nr_points,
                    "clobber": clobbered,
                    "relocs": relocs,
                    "pi": patch_instrs,
                    "b": bytes,
                    "l": locks,
                    "u": unlocks,
                    })

for s in samples:
#    print "%s %d %f %f %f %f %f %f %f %d %d %d" % (s["name"], s["nr_instrs"], s["tot"], s["ics"], s["bs"], s["sc"], s["r"], s["defect"], s["tot"] - s["sc"],
#                                                   s["np"], s["clobber"], s["relocs"])
#    print "%d %d %d %d %f" % (s["pi"], s["b"], s["l"], s["u"], s["tot"])
    print "%d %s" % (s["pi"] - s["l"] * 6 - s["u"] * 6 - s["nr_instrs"] - s["clobber"], s["name"])
