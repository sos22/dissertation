#! /usr/bin/env python

import sys

acc = 0
for f in map(float, sys.stdin.xreadlines()):
    acc += f
    print acc / 23559
