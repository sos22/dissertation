#! /usr/bin/env python

import sys
import util

figwidth = 12.5
figheight = 9

series = []

bubble_keys = ["compiling interfering CFG", "simplifying interfering CFG",
               "rederive crashing", "cross build", "cross simplify", "cross symbolic",
               "sat check"]

while True:
    l = util.get_line()
    if l == None:
        break
    s = {}
    s["early out"] = False
    s["satisfiable"] = False
    (sstart_time, words) = l
    if words != ["start", "interfering", "CFG"]:
        util.fail("lost sequence at %s" % str(l))

    while True:
        l = util.get_line()

        if l[1] == ["stop", "interfering", "CFG"]:
            end_time = l[0]
            break
        if l[1][0] == "unsatisfiable":
            s["satisfiable"] = False
            continue
        if l[1][0] == "satisfiable":
            s["satisfiable"] = True
            continue

        assert l[1][0] == "start"
        start_time = l[0]
        t = l[1][1:]
        l = util.get_line()
        assert l[1][0] == "stop"
        assert l[1][1:] == t
        k = " ".join(t)
        if k == "early-out":
            k = "rederive crashing"

        assert k in bubble_keys

        if not s.has_key(k):
            s[k] = { "dismiss": False,
                     "failed": False,
                     "time": 0 }
        s[k]["time"] += l[0] - start_time

        l = util.get_line()
        if l[1] in [["ic-atomic", "is", "false"], ["early", "out"]]:
            s[k]["dismiss"] = True
        elif l[1][0] == "failed":
            s[k]["failed"] = True
        else:
            util.lookahead = l
    if s.has_key("derive interfering CFGs") and not s.has_key("derive c-atomic"):
        s["derive c-atomic"] = { "dismiss": False, "failed": False, "time": 0 }
    series.append((end_time - sstart_time, s))

series.sort()

dilation = 35.0
(bubbles, max_time, max_nr_samples) = util.transpose_bubbles(series, dilation, bubble_keys)

y_centrums = {"compiling interfering CFG": 0.9,
              "simplifying interfering CFG": 0.75,
              "rederive crashing": 0.6,
              "early-out": 0.5,
              "cross build": 0.50,
              "cross simplify": 0.30,
              "cross symbolic": 0.90,
              "sat check": 0.15,
              "GC": 0.5,
              "defect": 0.5}

def scale_time(t):
    return t/110.0 * figwidth
def scale_idx(idx):
    return idx / float(max_nr_samples) * figheight

x_labels = []
for i in xrange(0,4):
    x_labels.append({"posn": scale_time(i * dilation), "label": "%d.0" % i})
    if i != 3:
        x_labels.append({"posn": scale_time((i + 0.5) * dilation), "label": "%d.5" % i})

util.print_preamble(x_labels, "Proportion of interfering \\glspl{cfg}", scale_time, 60, 10, figwidth, figheight)

labels = {"compiling interfering CFG": {"posn": ((0.5, 0.95), "right"),
                                        "label": "Compile interfering {\\StateMachine}"},
          "simplifying interfering CFG": {"posn": ((0.5, 0.83), "right"),
                                          "label": "Simplify interfering {\\StateMachine}"},
          "rederive crashing": {"posn": ((0.5, 0.70), "right"),
                                "label": "Rederive crashing {\\StateMachine}"},
          "cross build": {"posn": ((0.5, 0.50), "right"),
                          "label": "Build cross-product {\\StateMachine}"},
          "cross simplify": {"posn": ((0.5, 0.06), "right"),
                             "label": "Simplify cross-product {\\StateMachine}"},
          "cross symbolic": {"posn": ((2.5, 0.5), "above"),
                          "label": "\\shortstack[r]{Symbolically execute\\\\cross-product {\\StateMachine}}"},
          "sat check": {"posn": ((2.5, 0.06), "right"),
                        "label": "Final satisfiability check"},
          }
util.draw_bubbles(bubble_keys, bubbles, labels, y_centrums, scale_time, scale_idx, dilation, figheight, figwidth)
util.draw_line_series(scale_idx, scale_time, max_nr_samples, bubble_keys, bubbles, figwidth, figheight)
util.print_trailer(figwidth, figheight)
