#! /usr/bin/env python

import os
import sys
import re
import random

gen_vc_pat = re.compile("[0-9]*/[0-9]*: generated VC \([.0-9]*\)")

crashers = []
for f in os.listdir(sys.argv[1]):
    fle = file("%s/%s" % (sys.argv[1], f))
    acc = 0
    for l in fle.xreadlines():
        m1 = gen_vc_pat.match(l.strip())
        if m1:
            acc += 1
    fle.close()
    crashers.append(acc)

def gen_sample():
    acc = 0
    for i in xrange(len(crashers)):
        acc += crashers[random.randint(0, len(crashers) - 1)]
    return acc / float(len(crashers))

for i in xrange(10000):
    print gen_sample()
