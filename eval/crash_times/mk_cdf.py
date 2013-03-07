#! /usr/bin/env python

import sys

data = map(float, sys.stdin.readlines())
data.sort()

for i in xrange(len(data)):
    print "%f %f" % (data[i], i/float(len(data) - 1))
