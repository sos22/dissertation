#! /usr/bin/env python

import cPickle

c = file("data_cache.pkl", "r")
l = cPickle.load(c)
c.close()

for (alpha, data) in l.iteritems():
    print "alpha = %d ->" % alpha
    for d in data:
        print "\t%s" % str(d)
