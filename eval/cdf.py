#! /usr/bin/env python

import sys

extra = float(sys.argv[1])
data = map(float, sys.stdin.xreadlines())
data.sort()

for i in xrange(len(data)):
    print "%f %f" % (data[i], i / (len(data) + extra))
