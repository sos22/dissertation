#! /usr/bin/env python

import sys
import util

figwidth = 13
figheight = 9

series = []

while True:
    l = util.get_line()
    if l == None:
        break
    s = {}
    s["early out"] = False
    (start_time, words) = l
    if words != ["start", "crashing", "thread"]:
        util.fail("lost sequence at %s" % str(l))

    while True:
        l = util.get_line()
        if l[1] == ["finish", "crashing", "thread"]:
            end_time = l[0]
            break
        if l[1] == ["Dismiss", "early,", "PLT"]:
            end_time = l[0]
            s["early out"] = { "dismiss": True,
                               "failed": False,
                               "time": 0 }
            continue
        assert l[1][0] == "start"
        start_time = l[0]
        t = l[1][1:]
        l = util.get_line()
        assert l[1][0] == "stop"
        assert l[1][1:] == t
        k = " ".join(t)
        if not s.has_key(k):
            s[k] = { "dismiss": False,
                     "failed": False,
                     "time": 0 }
        s[k]["time"] += l[0] - start_time

        l = util.get_line()
        if l[1] in [["early", "out"], ["no", "interfering", "stores"]]:
            s[k]["dismiss"] = True
        elif l[1][0] == "failed":
            s[k]["failed"] = True
        else:
            util.lookahead = l
    if s.has_key("derive interfering CFGs") and not s.has_key("derive c-atomic"):
        s["derive c-atomic"] = { "dismiss": False, "failed": False, "time": 0 }
    series.append((end_time - start_time, s))

series.sort()

bubble_keys = ["early-out check", "build crashing CFG", "compile crashing machine", "simplify crashing machine", "derive c-atomic", "derive interfering CFGs", "process interfering CFGs"]
y_centrums = {"early-out check": 0.5,
              "build crashing CFG": 0.9,
              "compile crashing machine": 0.75,
              "simplify crashing machine": 0.5,
              "derive c-atomic": 0.25,
              "derive interfering CFGs": 0.5,
              "process interfering CFGs": 0.5}

dilation = 60
(bubbles, max_time, max_nr_samples) = util.transpose_bubbles(series, dilation, bubble_keys)

def scale_time(t):
    return t/700.0 * figwidth
def scale_idx(idx):
    return idx / float(max_nr_samples) * figheight

x_labels = []
for i in xrange(0,12):
    x_labels.append({"posn": scale_time(i * dilation), "label": "%d.0" % i})

util.print_preamble(x_labels, "Proportion of crashing instructions", scale_time, 300, 50, figwidth, figheight)

labels = {"build crashing CFG": {"posn": ((0.5, 0.95), "right"),
                                 "label": "Build crashing \\gls{cfg}"},
          "compile crashing machine": {"posn": ((1.5, .85), "right"),
                                       "label": "Compile crashing {\\StateMachine}"},
          "simplify crashing machine": {"posn": ((1.2, .3), "right"),
                                       "label": "Simplify crashing {\\StateMachine}"},
          "derive c-atomic": {"posn": ((1.2, .1), "right"),
                                       "label": "Derive C-atomic"},
          "derive interfering CFGs": {"posn": ((1.2, .48), "right"),
                                       "label": "Derive interfering \\glspl{cfg}"},
          "process interfering CFGs": {"posn": ((7.0, .6), "above"),
                                       "label": "Process interfering \\glspl{cfg}"}}
util.draw_bubbles(bubble_keys, bubbles, labels, y_centrums, scale_time, scale_idx, dilation, figheight)

util.draw_line_series(scale_idx, scale_time, max_nr_samples, bubble_keys, bubbles, figwidth, figheight)

util.print_trailer(figwidth, figheight)
