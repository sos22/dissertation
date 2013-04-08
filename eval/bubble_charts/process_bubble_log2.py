#! /usr/bin/env python

import sys
import util

figwidth = 12.5
figheight = 9

series = []

bubble_keys = ["compiling interfering CFG", "simplifying interfering CFG",
               "rederive crashing", "build ic-atomic", "simplify ic-atomic",
               "execute ic-atomic", "cross build", "cross simplify", "cross symbolic",
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

    cnt = 0

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
        start_time = l[0]
        k = " ".join(t)
        if k == "early-out":
            k = "rederive crashing"
        assert k in bubble_keys
        if not s.has_key(k):
            s[k] = { "dismiss": False,
                     "failed": False,
                     "time": 0 }

        l = util.get_line()
        if l[1] in [["timeout"], ["out", "of", "memory"]]:
            s[k]["failed"] = True
            s[k]["time"] += l[0] - start_time
            end_time = l[0]
            break
        else:
            assert l[1][0] == "stop"
            assert l[1][1:] == t
            s[k]["time"] += l[0] - start_time

            l = util.get_line()
            if l[1] in [["ic-atomic", "is", "false"], ["early", "out"]]:
                s[k]["dismiss"] = True
            else:
                util.lookahead = l
    if s.has_key("derive interfering CFGs") and not s.has_key("derive c-atomic"):
        s["derive c-atomic"] = { "dismiss": False, "failed": False, "time": 0 }

    series.append((end_time - sstart_time, s))

series.sort()

dilation = 150.0
(bubbles, max_time, max_nr_samples) = util.transpose_bubbles(series, dilation, bubble_keys)

y_centrums = {"compiling interfering CFG": 0.9,
              "simplifying interfering CFG": 0.75,
              "rederive crashing": 0.6,
              "early-out": 0.5,
              "build ic-atomic": 0.9,
              "simplify ic-atomic": 0.8,
              "execute ic-atomic": 0.9,
              "cross build": 0.5,
              "cross simplify": 0.25,
              "cross symbolic": 0.35,
              "sat check": 0.15,
              "GC": 0.5,
              "defect": 0.5}

def scale_time(t):
    return t/125.0 * figwidth
def scale_idx(idx):
    return idx / float(max_nr_samples) * figheight

x_labels = []
for i in xrange(0,9):
    x_labels.append({"posn": scale_time(i * dilation / 10.0), "label": "0.%d" % i})

util.print_preamble(x_labels, "Proportion of interfering \\glspl{cfg}", scale_time, 60, 10, figwidth, figheight)

labels = {"compiling interfering CFG": {"posn": ((0.14, 0.95), "right"),
                                        "label": "Compile interfering {\\StateMachine}"},
          "simplifying interfering CFG": {"posn": ((0.14, 0.83), "right"),
                                          "label": "Simplify interfering {\\StateMachine}"},
          "rederive crashing": {"posn": ((0.14, 0.70), "right"),
                                "label": "Rederive crashing {\\StateMachine}"},
          "build ic-atomic": {"posn": ((0.14, 0.60), "right"),
                              "label": "Build \\gls{ic-atomic} {\\StateMachine}"},
          "simplify ic-atomic": {"posn": ((0.14, 0.50), "right"),
                                 "label": "Simplify \\gls{ic-atomic} {\\StateMachine}"},
          "execute ic-atomic": {"posn": ((0.53, 0.37), "below left = 0"),
                                "label": "\\shortstack[r]{Symbolically execute\\\\ \\gls{ic-atomic} {\\StateMachine}}"},
          "cross build": {"posn": ((0.53, 0.19), "left"),
                          "label": "Build cross-product {\\StateMachine}"},
          "cross simplify": {"posn": ((0.53, 0.08), "left"),
                          "label": "\\shortstack[r]{Simplify cross-product\\\\{\\StateMachine}}"},
          "cross symbolic": {"posn": ((0.75, 0.55), "above"),
                             "label": "\\shortstack{Symbolically execute\\\\cross-product {\\StateMachine}}"},
          "sat check": {"posn": ((0.82, 0.06), "left"),
                        "label": "\\shortstack[r]{Final satisfia-\\\\bility check}"}
          }
util.draw_bubbles(bubble_keys, bubbles, labels, y_centrums, scale_time, scale_idx, dilation, figheight, figwidth)
util.draw_line_series(scale_idx, scale_time, max_nr_samples, bubble_keys, bubbles, figwidth, figheight)
util.print_trailer(figwidth, figheight)
