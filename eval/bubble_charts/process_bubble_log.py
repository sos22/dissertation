#! /usr/bin/env python

import sys
import util

simple_off = False
if len(sys.argv) > 1 and sys.argv[1] == "simple_off":
    simple_off = True

figwidth = 12.5
figheight = 9

bubble_keys = ["early-out check", "build crashing CFG", "compile crashing machine", "simplify crashing machine", "derive c-atomic", "derive interfering CFGs", "process interfering CFGs"]

series = []
while True:
    l = util.get_line()
    if l == None:
        break
    s = {}
    s["early out"] = False
    (sstart_time, words) = l
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
                               "failed": None,
                               "time": 0 }
            continue
        assert l[1][0] == "start"
        start_time = l[0]
        t = l[1][1:]
        k = " ".join(t)
        assert k in bubble_keys or k == "GC"
        if not s.has_key(k):
            s[k] = { "dismiss": False,
                     "failed": None,
                     "time": 0 }

        l = util.get_line()
        if l[1][0] == "timeout":
            s[k]["failed"] = "timeout"
            s[k]["time"] += l[0] - start_time
        else:
            assert l[1][0] == "stop"
            assert l[1][1:] == t
            s[k]["time"] += l[0] - start_time

            l = util.get_line()
            if l[1] in [["early", "out"], ["no", "interfering", "stores"]]:
                s[k]["dismiss"] = True
            else:
                util.lookahead = l
    if s.has_key("derive interfering CFGs") and not s.has_key("derive c-atomic"):
        s["derive c-atomic"] = { "dismiss": False, "failed": None, "time": 0 }
    series.append((end_time - sstart_time, s))

series.sort()

y_centrums = {"early-out check": 0.5,
              "build crashing CFG": 0.9,
              "compile crashing machine": 0.75,
              "simplify crashing machine": 0.5,
              "derive c-atomic": 0.13,
              "derive interfering CFGs": 0.3,
              "process interfering CFGs": 0.5,
              "defect": 0.5,
              "GC": 0.5}

if simple_off:
    dilation = 50
else:
    dilation = 35
(bubbles, max_time, max_nr_samples) = util.transpose_bubbles(series, dilation, bubble_keys)

def scale_time(t):
    if simple_off:
        return t/1250.0 * figwidth
    else:
        return t/125.0 * figwidth
def scale_idx(idx):
    return idx / float(max_nr_samples) * figheight

x_labels = []
if simple_off:
    for i in xrange(0,6,1):
        x_labels.append({"posn": scale_time(i * 5 * dilation), "label": "%d.0" % (i * 5)})
        if i != 5:
            x_labels.append({"posn": scale_time((i+.5) * 5 * dilation), "label": "%d.5" % (i * 5 + 2)})
else:
    for i in xrange(0,4):
        x_labels.append({"posn": scale_time(i * dilation), "label": "%d.0" % i})
        x_labels.append({"posn": scale_time((i+.5) * dilation), "label": "%d.5" % i})

if simple_off:
    util.print_preamble(x_labels, "Proportion of crashing instructions", scale_time, 600, 100, figwidth, figheight)
else:
    util.print_preamble(x_labels, "Proportion of crashing instructions", scale_time, 60, 10, figwidth, figheight)

if simple_off:
    labels = {"build crashing CFG": {"posn": ((2.5, 0.75), "right"),
                                     "label": "Build crashing \\gls{cfg}"},
              "compile crashing machine": {"posn": ((2.5, .60), "right"),
                                           "label": "Compile crashing {\\StateMachine}"},
              "derive c-atomic": {"posn": ((2.5, .12), "right"),
                                  "label": "Derive C-atomic"},
              "derive interfering CFGs": {"posn": ((2.5, .30), "right"),
                                          "label": "Derive interfering \\glspl{cfg}"},
              "process interfering CFGs": {"posn": ((22, .5), "above"),
                                           "label": "Process interfering \\glspl{cfg}"}
              }
else:
    labels = {"build crashing CFG": {"posn": ((0.2, 0.95), "right"),
                                     "label": "Build crashing \\gls{cfg}"},
              "compile crashing machine": {"posn": ((.5, .85), "right"),
                                           "label": "Compile crashing {\\StateMachine}"},
              "simplify crashing machine": {"posn": ((0.7, .40), "right"),
                                            "label": "Simplify crashing {\\StateMachine}"},
              "derive c-atomic": {"posn": ((0.7, .1), "right"),
                                  "label": "Derive C-atomic"},
              "derive interfering CFGs": {"posn": ((0.7, .25), "right"),
                                          "label": "Derive interfering \\glspl{cfg}"},
              "process interfering CFGs": {"posn": ((3.0, .5), "above"),
                                           "label": "Process interfering \\glspl{cfg}"}
              }

util.draw_bubbles(bubble_keys, bubbles, labels, y_centrums, scale_time, scale_idx, dilation, figheight, figwidth)

util.draw_line_series(scale_idx, scale_time, max_nr_samples, bubble_keys, bubbles, figwidth, figheight, include_oom = False)

util.print_trailer(figwidth, figheight)
