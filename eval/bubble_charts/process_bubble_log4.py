#! /usr/bin/env python

import sys
import util

figwidth = 12.5
figheight = 9

# The profiling produces much more detail than we need for the
# dissertation.  Merge some of the buckets.
do_merge = True
if do_merge:
    keymergemap = { "prepare summary": "slice by hb",
                    "canonicalise": "slice by hb",
                    "heuristic simplify": "slice by hb",
                    "happensBeforeMapT() constructor": "slice by hb",
                    "simplify plan": "place side conditions",
                    "compile": "gcc" }
else:
    keymergemap = {}
bubble_keys = ["canonicalise", "prepare summary", "slice by hb", "heuristic simplify",
               "happensBeforeMapT() constructor", "determine input availability",
               "place side conditions", "simplify plan", "build strategy",
               "compile", "gcc"]
bubble_keys = [k for k in bubble_keys if not keymergemap.has_key(k)]

series = []
while True:
    l = util.get_line()
    if l == None:
        break
    s = {}
    (sstart_time, words) = l
    if words != ["start", "build", "enforcer"]:
        util.fail("lost sequence at %s" % str(l))

    while True:
        l = util.get_line()
        if l[1] == ["stop", "build", "enforcer"]:
            end_time = l[0]
            break

        assert l[1][0] == "start"
        start_time = l[0]
        t = l[1][1:]
        l = util.get_line()
        assert l[1][0] == "stop"
        assert l[1][1:] == t
        k = " ".join(t)

        if keymergemap.has_key(k):
            k= keymergemap[k]

        assert k in bubble_keys

        if not s.has_key(k):
            s[k] = { "failed": False, "dismiss": False, "time": 0 }
        s[k]["time"] += l[0] - start_time

        l = util.get_line()
        if l[1][0] == "failed":
            s[k]["failed"] = True
        else:
            util.lookahead = l
    series.append((end_time - sstart_time, s))

series.sort()

dilation = 50.0
(bubbles, max_time, max_nr_samples) = util.transpose_bubbles(series, dilation, bubble_keys)
y_centrums = {"canonicalise": 0.9,
              "prepare summary": 0.5,
              "slice by hb": 0.8,
              "heuristic simplify": 0.7,
              "happensBeforeMapT() constructor": 0.6,
              "determine input availability": 0.70,
              "place side conditions": 0.5,
              "simplify plan": 0.3,
              "build strategy": 0.3,
              "compile": 0.1,
              "gcc": 0.1,
              "GC": 0.5,
              "defect": 0.5}

def scale_time(t):
    return t/60.0 * figwidth
def scale_idx(idx):
    return idx / float(max_nr_samples) * figheight

x_labels = []
for i in xrange(0,10,1):
    x_labels.append({"posn": scale_time(i * dilation * 0.1), "label": "0.%d" % i})
x_labels.append({"posn": scale_time(dilation), "label": "1.0"})

util.print_preamble(x_labels, "Proportion of interfering \\glspl{cfg}", scale_time, 60, 10, figwidth, figheight)

labels = {
          "slice by hb": {"posn": ((0.6, .9), "left"), "label": "\\shortstack[r]{Slice by happens-\\\\before graph}"},
          "determine input availability": { "posn": ((0.6, .6), "left"), "label": "Determine input availability"},
          "place side conditions": {"posn": ((0.6, .45), "left"), "label": "Place side-conditions"},
          "build strategy": {"posn": ((0.63, .23), "left"), "label": "Build patch strategy"},
          "gcc": {"posn": ((1.05, .17), "right"), "label": "\\shortstack[l]{Compiling\\\\enforcer}"},

          "prepare summary": {"posn": ((0.02, .8), "right"), "label": "Canonicalise"},
          "canonicalise": {"posn": ((0.02, .9), "right"), "label": "Canonicalise"},
          "heuristic simplify": { "posn": ((0.1, .6), "left"), "label": "Heuristic simplification"},
          "happensBeforeMapT() constructor": { "posn": ((0.1, .5), "left"), "label": "Build happens-before graphs"},
          "simplify plan": {"posn": ((0.1, .2), "left"), "label": "Simplify plan"},
          "compile": {"posn": ((0.2, .1), "right"), "label": "Compile?"},
          }
for k in keymergemap:
    del labels[k]
util.draw_bubbles(bubble_keys, bubbles, labels, y_centrums, scale_time, scale_idx, dilation, figheight, figwidth)

# And the timeout line
print "  \\draw [dashed] (0,%f)" % scale_idx(max_nr_samples)
for k in bubble_keys:
    bubble = bubbles[k]
    print "        -- (%f, %f)" % (scale_time(bubble["offset"]), scale_idx(max_nr_samples - bubble["dismiss"] - bubble["failed"]))
print "        ;"
# Legend
print "  \\node at (%f,%f) [right] {" % (scale_time(0.01 * dilation), figheight * 0.05)
print "      \\raisebox{1mm}{\\tikz{\\draw[dashed] (0,0) -- (1,0);}} Timeouts"
print "  };"

util.print_trailer(figwidth, figheight)
