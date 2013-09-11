#! /usr/bin/env python

import cPickle
import itertools
import math
import random

figwidth = 13
figheight = 3.7
timeout = 600.0
bar_width = 0.05 / figwidth
kboxheight = .25

y_res = 0.003

mintime = 0.00001
maxtime = timeout
nr_replicates = 1000

time_abscissae = [(0.00001, "0.00001", ""),
                  (0.0001, "0.0001", ""),
                  (0.001, "0.001", ""),
                  (0.01, "0.01", ""),
                  (0.1, "0.1", ""),
                  (1.0, "1", ""),
                  (10.0, "10", ""),
                  (100.0, "100", ""),
                  (600.0, "600", "[dashed]")]

alphas = [10,20,30,40,50,75,100]

data = {}
for alpha in alphas:
    with open("%s.pkl" % alpha) as f:
        data[alpha] = cPickle.load(f)

class IndentedFile:
    def __init__(self, underlying):
        self.underlying = underlying
        self._indent = 0
        self.atStartOfLine = True
    def indent(self):
        self._indent += 1
    def dedent(self):
        assert self._indent > 0
        self._indent -= 1

    def write(self, buf):
        if self.atStartOfLine:
            self.underlying.write(" " * (self._indent * 3))
            self.atStartOfLine = False
        if buf[-1] == "\n":
            endWithNewline = True
            buf = buf[:-1]
        else:
            endWithNewline = False
        buf = buf.replace("\n", "\n" + " " * (self._indent * 3))
        self.underlying.write(buf)
        if endWithNewline:
            self.atStartOfLine = True
            self.underlying.write("\n")

    def writeln(self, what):
        self.write(what)
        self.write("\n")

    def close(self):
        self.underlying.close()

def block(fle, name, options = ""):
    class foo:
        def __enter__(self):
            fle.writeln("\\begin{%s}%s" % (name, options))
            fle.indent();
        def __exit__(self, _exc_type, _exc_val, _exc_tb):
            fle.dedent();
            fle.writeln("\\end{%s}" % name)
    return foo()

# binomial coefficients
def nCr(n, r):
    num = reduce(operator.mul, xrange(n - r + 1, n + 1), 1)
    denum = reduce(operator.mul, xrange(1, r + 1), 1)
    assert num % denum == 0
    return num / denum

# log(nCr(n,r))
def lognCr(n, r):
    return sum(itertools.imap(math.log, xrange(n - r + 1, n + 1))) -\
        sum(itertools.imap(math.log, xrange(1, r + 1)))

def _binom_confidence_interval(nr_success, nr_attempts, interval):
    estimated_prob = float(nr_success) / nr_attempts
    sd = (nr_attempts * estimated_prob * (1 - estimated_prob)) ** .5
    def prob(outcome):
        # Anything more than 100 sigma from mean should be approximated to
        # zero, for general sanity and to avoid accumulating errors.
        if abs(nr_success - outcome) > sd * 100:
            return 0
        logProb = lognCr(nr_attempts, outcome) + outcome * math.log(estimated_prob) + (nr_attempts - outcome) * math.log(1 - estimated_prob)
        return math.e ** logProb

    thresh = (1 - interval) / 2

    # Lower bound
    lower = 0
    acc = 0
    while acc < thresh:
        acc += prob(lower)
        lower += 1

    # Upper bound
    upper = nr_attempts
    acc = 1
    while acc >= 1 - thresh:
        acc -= prob(upper)
        upper -= 1
    upper += 1
    return (estimated_prob, lower / float(nr_attempts), upper / float(nr_attempts))
def binom_confidence_interval(nr_success, nr_attempts, interval):
    if nr_success in [0, nr_attempts]:
        return "\\multicolumn{6}{c|}{%d/%d}" % (nr_success, nr_attempts)
    (_estimated_prob, lower, upper) = _binom_confidence_interval(nr_success, nr_attempts, interval)
    def f(x):
        return ("%.1f" % x).replace(".", "&")
    return "[&%s&%s&$]_{\\infty}^{%d}$\\%%" % (f(lower * 100), f(upper * 100), nr_attempts)

def float_range(lower, upper, step):
    lower = float(lower)
    upper = float(upper)
    step = float(step)
    while lower < upper:
        yield lower
        lower += step
def alpha_to_x(alpha):
    return alpha / 100.0
def time_to_y(mintime, maxtime):
    scale = math.log(maxtime / mintime)
    def t(time):
        return math.log(time / mintime) / scale
    def s(y):
        return math.e ** (y * scale) * mintime
    return (t, s)

def quantile(samples, q):
    assert 0 <= q <= 1
    idx = len(samples) * q
    idx0 = int(idx)
    idx1 = idx0 + 1
    idx = idx - idx0
    if idx1 == len(samples):
        return samples[-1]
    else:
        return samples[idx0] + (samples[idx1] - samples[idx0]) * idx

# Map from a value to the estimated quantile.
def inv_quantile(samples, val):
    val = float(val) # For sanity

    # Find the last element which is <= val.
    lower = 0
    upper = len(samples)
    while True:
        guess = (lower + upper) / 2
        if guess == lower or guess == upper:
            break
        if samples[guess] < val:
            lower = guess
        else:
            upper = guess
    # Linear scan for the last little bit.
    idx = lower
    while idx >= 0 and samples[idx] > val:
        idx -= 1
    while idx < len(samples) - 1 and samples[idx+1] <= val:
        idx += 1

    if idx == -1:
        # Past lower bound -> just use 0.0
        res = 0.0
    elif idx >= len(samples) - 1:
        # Past upper bound
        res = 1.0
    elif samples[idx+1] == val:
        # Special case when we have samples equal to @val
        idx2 = idx + 1
        while samples[idx2] == val:
            idx2 += 1
        res = (idx2 + idx) / (2.0 * len(samples))
    else:
        # Otherwise, linear interpolate.
        pt0 = (idx / float(len(samples)), samples[idx])
        pt1 = ((idx+1.0) / len(samples), samples[idx+1])
        assert pt0[1] <= val
        assert pt1[1] > pt0[1]
        assert pt1[0] > pt0[0]
        res = (pt1[0] - pt0[0]) * (val - pt0[1]) / float(pt1[1] - pt0[1]) + pt0[0]
    return res

def draw_mean_bars(output, xcoord, mean_low, mean, mean_high, use_circle = False):
    output.writeln("\\draw (%f,%f) -- (%f,%f);" % (xcoord, mean_low, xcoord, mean_high))
    output.writeln("\\draw (%f,%f) -- (%f,%f);" % (xcoord-bar_width, mean_low,
                                                   xcoord+bar_width, mean_low))
    output.writeln("\\draw (%f,%f) -- (%f,%f);" % (xcoord-bar_width, mean_high,
                                                   xcoord+bar_width, mean_high))
    if use_circle:
        output.writeln("\\draw (%f,%f) circle(%f);" % (xcoord, mean, bar_width))
    else:
        output.writeln("\\draw (%f,%f) -- (%f,%f);" % (xcoord-bar_width, mean-bar_width,
                                                       xcoord+bar_width, mean+bar_width))
        output.writeln("\\draw (%f,%f) -- (%f,%f);" % (xcoord-bar_width, mean+bar_width,
                                                       xcoord+bar_width, mean-bar_width))

def draw_pdf(output, samples, xcoord, xscale, sample_to_y, y_to_sample, upper_bound, nr_failed):
    mean = sum(samples)/len(samples)

    # Convert samples to y values.
    samples = [sample_to_y(s) for s in samples]
    if upper_bound != None:
        upper_bound = sample_to_y(upper_bound)
    mean = sample_to_y(mean)

    # Compute a bandwidth.
    iqr = quantile(samples, 0.75) - quantile(samples, 0.25)
    sd = iqr / 1.34
    if iqr == 0:
        # inter-quartile range is empty -> fallback to an SD-based
        # bandwidth estimate.
        sd = (sum( (x - mean) ** 2 for x in samples ) / len(samples)) ** .5
    bandwidth = 3.69 * sd / (len(samples) ** .2) / 2
    del iqr
    del sd

    line_decoration = ""
    error_decoration = "[color=black!50]"

    print "Selected bandwidth %f" % bandwidth
    def _val_to_density(val, samples):
        if upper_bound != None and val > upper_bound:
            return 0.0
        b = bandwidth / 2
        if upper_bound == None or val + b < upper_bound:
            lower = val - b
            upper = val + b
        else:
            width = 2 * (upper_bound - val)
            width *= bandwidth
            width **= .5
            upper = upper_bound - width
            lower = upper_bound
        res = (inv_quantile(samples, upper) - inv_quantile(samples, lower)) / (upper - lower)
        return res
    def val_to_density(val):
        return _val_to_density(val, samples)
    densities = [(val, val_to_density(val)) for val in float_range(0, 1, y_res)]

    # Bootstrap error bars.
    def generate_alternate():
        r = [random.choice(samples) for _ in samples]
        r.sort()
        return r
    alts = [generate_alternate() for _ in xrange(nr_replicates)]
    alt_means = [sample_to_y(sum(map(y_to_sample, alt))/len(alt)) for alt in alts]
    alt_means.sort()
    def density_range(val):
        reps = [_val_to_density(val, alt) for alt in alts]
        reps.sort()
        return (quantile(reps, 0.05), quantile(reps, 0.95))
    error_ranges = [(val, density_range(val)) for val in float_range(0, 1, y_res)]

    def draw_body(leader):
        output.write("%s\n" % leader)
        output.indent()
        lastwidth = 0
        first = True
        for (y, width) in densities:
            if abs(width - lastwidth) > 0.01 * xscale:
                if not first:
                    output.write("-- ")
                first = False
                output.writeln("(%f,%f)" % (xcoord - width * xscale, y))
                lastwidth = width
        lastwidth = -width
        for (y, width) in reversed(densities):
            if abs(width - lastwidth) > 0.01 * xscale:
                output.writeln("-- (%f,%f)" % (xcoord + width * xscale, y))
                lastwidth = width
        output.writeln("-- cycle;")
        output.dedent()

    with block(output, "pgfonlayer", "{bg}"):
        draw_body("\\fill [color=white]")

    output.write("\\fill %s\n" % error_decoration)
    output.indent()
    first = True
    for (y, (lower, _upper)) in error_ranges:
        if not first:
            output.write("-- ")
        first = False
        output.writeln("(%f,%f)" % (xcoord - lower * xscale, y))
    for (y, (_lower, upper)) in reversed(error_ranges):
        output.writeln("-- (%f,%f)" % (xcoord - upper * xscale, y))
    output.writeln(";")
    output.dedent()
    output.write("\\fill %s\n" % error_decoration)
    output.indent()
    first = True
    for (y, (lower, _upper)) in error_ranges:
        if not first:
            output.write("-- ")
        first = False
        output.writeln("(%f,%f)" % (xcoord + lower * xscale, y))
    for (y, (_lower, upper)) in reversed(error_ranges):
        output.writeln("-- (%f,%f)" % (xcoord + upper * xscale, y))
    output.writeln(";")
    output.dedent()

    draw_body("\\draw %s" % line_decoration)

    # Mean and bars
    mean_low = quantile(alt_means, 0.05)
    mean_high = quantile(alt_means, 0.95)
    draw_mean_bars(output, xcoord, mean_low, mean, mean_high)

    # And the kernel
    output.writeln("\\draw %s (%f,%f) rectangle (%f,%f);" % (line_decoration,
                                                             xcoord - xscale / (bandwidth * (len(samples) + nr_failed) * 2),
                                                             -kboxheight / 2 - bandwidth / 2,
                                                             xcoord + xscale / (bandwidth * (len(samples) + nr_failed) * 2),
                                                             -kboxheight / 2 + bandwidth / 2))

def draw_alpha_field(output, sep):
    with block(output, "pgfonlayer", "{bg}"):
        for alpha in alphas:
            x = alpha_to_x(alpha)
            output.writeln("\\draw [color=black!10] (%f,0) -- (%f,1);" % (x, x))
    with block(output, "pgfonlayer", "{fg}"):
        output.writeln("\\draw[->] (0,%f) -- (1,%f);" % (sep, sep))
        for alpha in alphas:
            x = alpha_to_x(alpha)
            output.writeln("\\node at (%f,%f) [below] {%d};" % (x, sep, alpha))
        output.writeln("\\node at (.5,%f) [below] {\\gls{alpha}};" % (sep - .15))
def draw_time_field(output, time_abscissae, time_to_y, label, failed, kernel):
    with block(output, "pgfonlayer", "{bg}"):
        for time in time_abscissae:
            y = time_to_y(time[0])
            output.writeln("\\draw [color=black!10] %s (0,%f) -- (1,%f);" % (time[2], y, y))
    with block(output, "pgfonlayer", "{fg}"):
        for time in time_abscissae:
            y = time_to_y(time[0])
            output.writeln("\\node at (0,%f) [left] {%s};" % (y, time[1]))
        if kernel:
            output.writeln("\\node at (0,%f) [left] {Kernel};" % (-kboxheight / 2))
        output.writeln("\\draw[->] (0,0) -- (0,1);")

def draw_field(output, time_abscissae, time_to_y):
    draw_alpha_field(output, - kboxheight)
    draw_time_field(output, time_abscissae, time_to_y, "Time taken, seconds", True, True)

def after_rerun(x):
    if isinstance(x[2], tuple):
        return x[2][1]
    else:
        return x
def after_rerun2(x):
    if isinstance(x[1], tuple):
        return x[1][1]
    else:
        return x

output = IndentedFile(file("time_per_crashing.tex", "w"))
with block(output, "tikzpicture"):
    output.writeln("%% Gross time taken per potentially-crashing instruction")
    with block(output, "scope", "[xscale=%f,yscale=%f]" % (figwidth, figheight)):
        output.writeln("\\useasboundingbox (-.13,-.4) rectangle (1.0,1.0);")
        with block(output, "pgfonlayer", "{bg}"):
            output.writeln("\\fill [color=white] (0,0) rectangle (1,1);")
        (t, s) = time_to_y(mintime, maxtime)
        draw_field(output, time_abscissae, t)
        # PDF of time taken per crashing instruction, after re-runs.
        for alpha in alphas:
            ar = map(after_rerun, data[alpha].itervalues())
            samples = [r[0] for r in ar if r[2] != "timeout" and not isinstance(r[2], tuple)]
            samples.sort()
            print "Average for crashing alpha = %d -> %f" % (alpha, sum(samples) / len(samples))
            nr_rerun = len([r for r in ar if r[2] == "timeout" or isinstance(r[2], tuple)])
            draw_pdf(output, samples, alpha_to_x(alpha), 0.007, t, s, timeout, nr_rerun)
output.close()

output = IndentedFile(file("time_per_interfering.tex", "w"))
with block(output, "tikzpicture"):
    with block(output, "scope", "[xscale=%f,yscale=%f]" % (figwidth, figheight)):
        output.writeln("\\useasboundingbox (-.13,-.4) rectangle (1.0,1.0);")
        (t, s) = time_to_y(0.001, maxtime)
        with block(output, "pgfonlayer", "{bg}"):
            output.writeln("\\fill [color=white] (0,0) rectangle (1,1);")
        draw_field(output, [x for x in time_abscissae if x[0] >= 0.001], t)
        for alpha in alphas:
            ar = map(after_rerun, data[alpha].itervalues())
            arrs = [r[2] for r in ar if r[2] != "timeout" and not isinstance(r[2], tuple)]
            samples = []
            ar = []
            for arr in arrs:
                ar += map(after_rerun2, arr.itervalues())
            samples = [r[0] for r in ar if r != None and r[1] in ["satisfiable", "unsatisfiable"]]
            samples.sort()
            nr_failed = len([r for r in ar if r != None and not r[1] in ["satisfiable", "unsatisfiable"]])
            print "Average for interfering alpha = %d -> %f" % (alpha, sum(samples) / len(samples))
            draw_pdf(output, samples, alpha_to_x(alpha), 0.007, t, s, timeout, nr_failed)
output.close()

output = IndentedFile(file("interfering_per_crashing.tex", "w"))
with block(output, "tikzpicture"):
    with block(output, "scope", "[xscale=%f,yscale=%f]" % (figwidth / 2, 3.5)):
        output.writeln("\\useasboundingbox (-.1,-.2) rectangle (1.1,1.05);")
        with block(output, "pgfonlayer", "{bg}"):
            output.writeln("\\fill [color=white] (0,0) rectangle (1,1);")
        def cnt_to_y(cnt):
            return cnt / 7.0
        def y_to_cnt(y):
            return y * 7.0
        draw_alpha_field(output, 0)
        draw_time_field(output,
                        [(a, str(a), "") for a in xrange(8)],
                        cnt_to_y,
                        "",
                        False,
                        False)
        
        for alpha in alphas:
            ar = map(after_rerun, data[alpha].itervalues())
            samples = [float(len(r[2])) for r in ar if r[2] != "timeout" and not isinstance(r[2], tuple)]
            samples.sort()
            print "Average nr interfering for alpha = %d -> %f" % (alpha, sum(samples) / len(samples))
            def generate_alternate():
                r = [random.choice(samples) for _ in samples]
                r.sort()
                return r
            alts = [generate_alternate() for _ in xrange(nr_replicates)]
            alt_means = [sum(alt)/len(alt) for alt in alts]
            alt_means.sort()
            draw_mean_bars(output,
                           alpha_to_x(alpha),
                           cnt_to_y(quantile(alt_means, 0.05)),
                           cnt_to_y(sum(samples) / len(samples)),
                           cnt_to_y(quantile(alt_means, 0.95)))
output.close()

output = IndentedFile(file("vcs_per_interfering.tex", "w"))
with block(output, "tikzpicture"):
    with block(output, "scope", "[xscale=%f,yscale=%f]" % (figwidth / 2, 3.5)):
        output.writeln("\\useasboundingbox (-.15,-.2) rectangle (1.05,1.05);")
        with block(output, "pgfonlayer", "{bg}"):
            output.writeln("\\fill [color=white] (0,0) rectangle (1,1);")
        maxfrac = .30
        def frac_to_y(frac):
            return frac / maxfrac
        def y_to_frac(y):
            return y * maxfrac
        draw_alpha_field(output, 0)
        draw_time_field(output,
                        [(0.01 * x, "%d\\%%" % x, "") for x in xrange(0,31,5)],
                        frac_to_y,
                        "",
                        False,
                        False)
        for alpha in alphas:
            ar = map(after_rerun, data[alpha].itervalues())
            arrs = [r[2] for r in ar if r[2] != "timeout" and not isinstance(r[2], tuple)]
            samples = []
            ar = []
            for arr in arrs:
                ar += map(after_rerun2, arr.itervalues())
            nr_pass = len([r for r in ar if r != None and r[1] == "satisfiable"])
            (estimated_prob, lower, upper) = _binom_confidence_interval(nr_pass, len(ar), 0.9)
            print "Frac generating VCs = %d -> %f" % (alpha, estimated_prob)
            draw_mean_bars(output,
                           alpha_to_x(alpha),
                           frac_to_y(lower),
                           frac_to_y(estimated_prob),
                           frac_to_y(upper),
                           True)
output.close()

output = IndentedFile(file("failures.tex", "w"))
colspec = ">{~~}r@{}r@{.}l@{,~}r@{.}l@{}l<{~~}"
with block(output, "tabular", "{|p{1cm}|%s|%s|%s|}" % (colspec, colspec, colspec)):
    output.writeln("\\hline")
    output.writeln(r"$\alpha$ & \multicolumn{6}{c|}{Phase \subcrash{}} & \multicolumn{6}{c|}{Phase \subinterfering{}} & \multicolumn{6}{c|}{Both phases} \\")
    output.writeln("\\hline")
    for alpha in alphas:
        output.write("%d & " % alpha)
        # Crashing failure rate
        d = data[alpha]
        nr_attempts = len(d)
        nr_failures = 0
        for c in d.itervalues():
            c = after_rerun(c)
            if not isinstance(c[2], dict):
                nr_failures += 1
        output.write("%s & " % binom_confidence_interval(nr_failures, nr_attempts, 0.9))
        # Interfering failure rate
        nr_attempts = 0
        nr_failures = 0
        for c in d.itervalues():
            c = after_rerun(c)
            if not isinstance(c[2], dict):
                continue
            nr_attempts += len(c[2])
            for i in c[2].itervalues():
                i = after_rerun2(i)
                if i == None or i[1] == "timeout" or (isinstance(i[1], tuple) and i[1][0] == "oom"):
                    nr_failures += 1
        output.write("%s & " % binom_confidence_interval(nr_failures, nr_attempts, 0.9))
        # Composite rate.  This is a little more tricky.
        cks = data.keys()
        def gen_replicate():
            nr_attempts = 0
            nr_failures = 0
            cs = map(after_rerun, d.itervalues())
            nonFailedCs = filter(lambda c: isinstance(c[2], dict), cs)
            for _c in d:
                c = random.choice(cs)
                if not isinstance(c[2], dict):
                    preFailed = True
                    c = random.choice(nonFailedCs)
                else:
                    preFailed = False
                iis = map(after_rerun2, c[2].itervalues())
                nr_attempts += len(iis)
                if preFailed:
                    nr_failures += len(iis)
                else:
                    for i in c[2]:
                        i = random.choice(iis)
                        if i == None or i[1] == "timeout" or (isinstance(i[1], tuple) and i[1][0] == "oom"):
                            nr_failures += 1
            return float(nr_failures)/nr_attempts
        replicates = [gen_replicate() for _ in xrange(nr_replicates)]
        replicates.sort()
        def f(x):
            return ("%.1f" % x).replace(".", "&")
        output.write(r"[&%s&%s&$]_{%d}$\%% " % (f(quantile(replicates, 0.05) * 100),
                                                f(quantile(replicates, 0.95) * 100),
                                                nr_replicates))
        output.writeln(r"\\")
        print "Done alpha = %d" % alpha
    output.writeln("\\hline")
output.close()
