#! /usr/bin/env python

import sys
import math
import decimal

figwidth = 5.5
figheight = 5.0

logscale = True

class indented_file(object):
    def __init__(self, f):
        self.f = f
        self.indent = 0
    def write(self, what):
        self.f.write(what.replace("\n", "\n" + " " * self.indent))
    def writeln(self, what):
        self.write(what + "\n")

    def close(self):
        self.f.close()

def draw_cdf(output, fname, label, lower_data_limit, upper_data_limit):
    output.writeln("\\subfigure[][%s]{" % label)
    output.indent += 1
    output.writeln("\!\!\!\\begin{tikzpicture}")

    with file(fname) as f:
        data = sorted(map(float, f.xreadlines()))

    yscale = figheight / len(data)
    mind = min(lower_data_limit, min(data))
    maxd = min(max(data), upper_data_limit)
    if logscale:
        xscale = figwidth / math.log(maxd / mind)
        def scale_x(x):
            return math.log(x / mind) * xscale
        def _xlabels(start, end):
            while start < end * 1.1:
                yield start
                start *= 2
        xlabels = _xlabels(mind, maxd)
    else:
        xscale = figwidth / (maxd - mind)
        def scale_x(x):
            return (x - mind) * xscale
        xlabels = xrange(mind, maxd, (maxd - mind) / 10)

    mean = float(sum(data)) / len(data)
    sd = (sum([(x - mean)**2 for x in data]) / (len(data) * (len(data) - 1))) ** .5

    # Draw the field
    for ylabel in xrange(0,101, 20):
        y = ylabel * len(data) * yscale / 100.0
        output.writeln("\\draw [color=black!10] (%f, %f) -- (%f, %f);" % (0, y, figwidth, y))
        output.writeln("\\node at (%f, %f) [left] {%d\\%%};" % (0, y, ylabel))
    for xlabel in xlabels:
        x = scale_x(xlabel)
        output.writeln("\\draw [color=black!10] (%f, %f) -- (%f, %f);" % (x, 0, x, figheight))
        output.writeln("\\node at (%f, %f) [below] {%d};" % (x, 0, xlabel))

    # Error region of mean.
    output.writeln("\\fill [color=black!40] (%f, %f) rectangle (%f,%f);" % (scale_x(max(mean - sd, mind)), 0,
                                                                            scale_x(mean + sd), figheight))

    # Error region for CDF
    dkw_bound = ((-math.log(0.9/2) / (2.0 * len(data))) ** .5) * len(data)
    idx = 0
    while idx < len(data) and data[idx] <= maxd:
        idx2 = idx + 1
        while idx2 < len(data) and data[idx2] == data[idx]:
            idx2 += 1
        
        lower = max(0, idx2 - dkw_bound) * yscale
        upper = min(len(data), idx2 + dkw_bound) * yscale
        left = scale_x(data[idx])
        if idx2 == len(data) or data[idx2] >= maxd:
            right = figwidth
        else:
            right = scale_x(data[idx2])
        output.writeln("\\fill [color=black!50] (%f, %f) rectangle (%f, %f);" % (left, lower,
                                                                                 right, upper))
        idx = idx2

    # Mean
    output.writeln("\\draw (%f, %f) -- (%f, %f);\n" % (scale_x(mean), 0, scale_x(mean), figheight))
    sd = decimal.Decimal(str(sd))
    digits = pow(10, (sd.log10() - decimal.Decimal(".5")).to_integral())
    mean2 = (decimal.Decimal(str(mean)) / digits).quantize(decimal.Decimal("1")) * digits
    sd2 = (sd / digits).quantize(decimal.Decimal("1")) * digits
    print "Round %f pm %f -> %s pm %s" % (mean, sd, mean2, sd2)
    output.writeln("\\node at (%f, %f) [above] {$%s \pm_{\mu}^{%d} %s$};" % (scale_x(mean), figheight,
                                                                             mean2, len(data), sd2))

    # CDF
    idx = 0
    while idx < len(data) and data[idx] <= maxd:
        idx2 = idx + 1
        while idx2 < len(data) and data[idx2] == data[idx]:
            idx2 += 1
        
        left = scale_x(data[idx])
        if idx2 == len(data) or data[idx2] >= maxd:
            right = figwidth
        else:
            right = scale_x(data[idx2])
        y = (idx2-1) * yscale
        output.writeln("\\draw (%f, %f) -- (%f, %f);" % (left, y,
                                                         right, y))
        idx = idx2

# Axes last
    output.writeln("\\draw[->] (%f, %f) -- (%f,%f);" % (0, 0, figwidth, 0))
    output.writeln("\\draw[->] (%f, %f) -- (%f,%f);" % (0, 0, 0, figheight))

    output.indent -= 1
    output.writeln("\\end{tikzpicture}")
    output.indent -= 1
    output.writeln("}")
    output.indent -= 1
    

output = indented_file(file("structure_complexity.tex", "w"))
output.indent += 1
output.writeln("\\begin{tabular}{ll}")
draw_cdf(output, "instrs_per_probe", "Instructions per crashing \\gls{cfg}", 20, 320)
output.writeln("&")
draw_cdf(output, "states_per_probe1", "States per crashing {\StateMachine}, before simplification", 50, 1000)
output.writeln("\\\\")
draw_cdf(output, "states_per_probe2", "States per crashing {\StateMachine}, after simplification", 1, 100)
output.writeln("&")
draw_cdf(output, "interfering_per_crashing", "Interfering \glspl{cfg} per crashing {\StateMachine}", 1, 100)
output.indent -= 1
output.writeln("\\end{tabular}")

output.close()

