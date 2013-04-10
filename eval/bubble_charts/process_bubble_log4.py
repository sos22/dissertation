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
    if words[:-1] != ["start", "build", "enforcer"]:
        util.fail("lost sequence at %s" % str(l))

    cnt = 0
    while True:
        l = util.get_line()
        if l[1] == ["stop", "build", "enforcer"]:
            end_time = l[0]
            break

        assert l[1][0] == "start"
        start_time = l[0]
        t = l[1][1:]
        k = " ".join(t)
        if keymergemap.has_key(k):
            k = keymergemap[k]
        assert k in bubble_keys
        if not s.has_key(k):
            s[k] = { "failed": None, "dismiss": False, "time": 0 }

        l = util.get_line()
        s[k]["time"] += l[0] - start_time
        cnt += l[0] - start_time
        if l[1] == ["out", "of",  "memory"]:
            s[k]["failed"] = "memory"
            end_time = l[0]
            break
        elif l[1] == ["timeout"]:
            s[k]["failed"] = "timeout"
            end_time = l[0]
            break
        else:
            assert l[1][0] == "stop"
            assert l[1][1:] == t
    series.append((end_time - sstart_time, s))

series.sort()

dilation = 100.0
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
              "defect": 0.3}

def scale_time(t):
    return t/60.0 * figwidth
def scale_idx(idx):
    return idx / float(max_nr_samples) * figheight

x_labels = []
for i in xrange(0,65,5):
    x_labels.append({"posn": scale_time(i * dilation * 0.01), "label": "0.%02d" % i})
x_labels.append({"posn": scale_time(dilation), "label": "1.0"})

util.print_preamble(x_labels, "Proportion of interfering \\glspl{cfg}", scale_time, 60, 10, figwidth, figheight)

labels = {
          "slice by hb": {"posn": ((0.28, .88), "left"), "label": "Slice by happens-before graph"},
          "determine input availability": { "posn": ((0.28, .6), "left"), "label": "\\shortstack[r]{Determine input\\\\availability}"},
          "place side conditions": {"posn": ((0.28, .40), "left"), "label": "Place side-conditions"},
          "build strategy": {"posn": ((0.28, .2), "left"), "label": "Build patch strategy"},
          "gcc": {"posn": ((0.55, .2), "right"), "label": "\\shortstack[l]{Compile\\\\enforcer}"},

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
    print "        -- (%f, %f)" % (scale_time(bubble["offset"]), scale_idx(max_nr_samples - bubble["dismiss"] - bubble["timeout"]))
print "        ;"
# And the OOM line
print "  \\draw [dotted] (0,%f)" % scale_idx(max_nr_samples)
for k in bubble_keys:
    bubble = bubbles[k]
    print "        -- (%f, %f)" % (scale_time(bubble["offset"]), scale_idx(max_nr_samples - bubble["dismiss"] - bubble["timeout"] - bubble["oom"]))
print "        ;"
# Legend
print "  \\node at (%f,%f) [right] {\\shortstack[l]{" % (scale_time(0.01 * dilation), figheight * 0.05)
print "      \\raisebox{1mm}{\\tikz{\\draw[dashed] (0,0) -- (1,0);}} Timeout\\\\"
print "      \\raisebox{1mm}{\\tikz{\\draw[dashed] (0,0) -- (1,0);}} Out of memory"
print "  }};"

util.print_trailer(figwidth, figheight)
