import sys
import os
import math
import cPickle
import random

cache = "data_cache.pkl"

figheight = 10.0
figwidth = 11.0
legendwidth = 2.5
box_width = 0.5

mintime = 0.01

def fail(msg):
    sys.stderr.write("%s\n" % msg)

def parse_interfering(path, l, cntr):
    line = l.readline().strip()
    if line == "":
        return None
    sample = {}
    sample["gvc_oom"] = False
    sample["gvc_timeout"] = False
    sample["early-out"] = False
    sample["generated_vc"] = None
    sample["gvc_time"] = None
    if line == "Child timed out in run_in_child":
        sample["gvc_timeout"] = True
        return sample
    w = line.split()[1:]
    if len(w) != 5 or w[:3] != ["Interfering", "CFG", "has"]:
        fail("%s got bad ich line %s" % (path, line))
    assert cntr == int(line.split()[0].split("/")[0])
    sample["nr_instrs"] = int(w[3])

    line = l.readline().strip()
    if line == "Child timed out in run_in_child":
        sample["gvc_timeout"] = True
        return sample
    w = line.split()[1:]
    if w == ["single", "store", "versus", "single", "shared", "load"]:
        sample["early-out"] = True
        sample["generated_vc"] = False
        return sample
    if len(w) != 6 or w[:4] != ["Initial", "interfering", "StateMachine", "has"]:
        fail("%s got bad ich2 line %s" % (path, line))
    sample["initial_interfering_states"] = int(w[4])
                
    line = l.readline().strip()
    if line == "OOM kill in checkWhetherInstructionCanCrash()":
        sample["gvc_oom"] = True
        return sample
    if line == "Child timed out in run_in_child":
        sample["gvc_timeout"] = True
        return sample
    w = line.split()[1:]
    if len(w) != 6 or w[:4] != ["Simplified", "interfering", "StateMachine", "has"]:
        fail("%s got bad ich3 line %s" % (path, line))
    sample["simplified_interfering_states"] = int(w[4])

    line = l.readline().strip()
    w = line.split()[1:]
    if len(w) != 3 or w[:2] != ["buildStoreMachine", "took"]:
        fail("%s got bad ich4 line %s" % (path, line))
    sample["bsm_time"] = float(w[2])

    line = l.readline().strip()
    if line == "Child timed out in run_in_child":
        sample["gvc_timeout"] = True
        return sample

    w = line.split()[1:]
    if line == "OOM kill in checkWhetherInstructionCanCrash()":
        sample["gvc_oom"] = True
        return sample
    if w[:-1] in [["single", "store", "versus", "single", "load,", "after", "localise"],
                  ["generated", "VC"],
                  ["crash", "impossible"],
                  ["IC", "is", "false"]]:
        t = float(w[-1][1:-1])
        sample["gvc_time"] = t
        sample["gvc_timeout"] = False
        sample["generated_vc"] = w[:-1] == ["generated", "VC"]
        return sample
    fail("Huh? %s, %s" % (path, line))

def parse_crashing(path, l, start_cntr = 0):
    sample = {}
    sample["nr_crashing_instrs"] = None
    sample["initial_crashing_states"] = None
    sample["simplified_crashing_states"] = None
    sample["gvc_time"] = None
    sample["gvc_timeout"] = None
    sample["generated_vc"] = None

    line = l.readline().strip()
    if line != "Start processing":
        fail("Expected start processing line in %s, got %s" % (path, line))
    line = l.readline().strip()
    if line == "Early out":
        sample["early-out"] = True
        l.close()
        return sample
    sample["early-out"] = False

    if line == "Child timed out in run_in_child":
        sample["bpm_timeout"] = True
        sample["bpm_oom"] = False
        return sample
    w = line.split()
    if len(w) != 5 or w[0:3] != ["Crashing", "CFG", "has"] or w[-1] != "instructions":
        fail("%s doesn't start with CChi line (%s)" % (path, line))
    sample["nr_crashing_instrs"] = int(w[3])
    if int(w[3]) < 10:
        fail("%s has too few instructions (%s)" % (path, line))
    assert int(w[3]) >= 10

    line = l.readline().strip()
    if line == "Child timed out in run_in_child":
        sample["bpm_timeout"] = True
        sample["bpm_oom"] = False
        return sample
    w = line.split()
    if len(w) != 6 or w[0:4] != ["Initial", "crashing", "machine", "has"] or w[-1] != "states":
        fail("%s missing ICMS line (%s)" % (path, line))
    sample["initial_crashing_states"] = int(w[4])

    line = l.readline().strip()
    if line in ["Child failed in run_in_child, signal 11", "OOM kill in checkWhetherInstructionCanCrash()", ""]:
        sample["bpm_oom"] = True
        sample["bpm_timeout"] = False
        return sample
    if line == "Child timed out in run_in_child":
        sample["bpm_timeout"] = True
        sample["bpm_oom"] = False
        return sample
    w = line.split()
    if len(w) != 6 or w[0:4] != ["Simplified", "crashing", "machine", "has"] or w[-1] != "states":
        fail("%s missing SCMS line (%s)" % (path, line))
    sample["simplified_crashing_states"] = int(w[4])

    line = l.readline().strip()
    w = line.split()
    if len(w) != 3 or w[0] != "buildProbeMachine" or w[1] != "took":
        fail("%s doesn't start with bpm line (%s)" % (path, line))
    sample["bpm_oom"] = False
    sample["bpm_timeout"] = False
    sample["bpm_time"] = float(w[2])

    line = l.readline().strip()
    if line in ["no conflicting stores", "No conflicting stores (1847)", "No conflicting stores (1825)"]:
        sample["skip_gsc"] = True
        return sample
    sample["skip_gsc"] = False
    if line == "OOM kill in checkWhetherInstructionCanCrash()" or line == "Child failed in run_in_child, signal 6":
        sample["gsc_oom"] = True
        sample["gsc_timed_out"] = False
        return sample
    if line == "Child timed out in run_in_child":
        sample["gsc_oom"] = False
        sample["gsc_timed_out"] = True
        return sample
    w = line.split()
    if len(w) != 3 or w[0] != "atomicSurvivalConstraint" or w[1] != "took":
        fail("%s lacks an ASC line (%s)" % (path, line))
    sample["asc_time"] = float(w[2])

    line = l.readline().strip()
    if line == "Child timed out in run_in_child":
        sample["gsc_timed_out"] = True
        sample["gsc_oom"] = False
        return sample
    if line == "OOM kill in checkWhetherInstructionCanCrash()":
        sample["gsc_oom"] = True
        sample["gsc_timed_out"] = False
        return sample
    w = line.split()
    if len(w) != 6 or w[0] != "getStoreCFGs" or w[1] != "took" or w[3] != "seconds," or w[4] != "produced":
        fail("%s lacks a GSC line (%s)" % (path, line))
    sample["gsc_timed_out"] = False
    sample["nr_store_cfgs"] = int(w[5])
    sample["gsc_oom"] = False
    sample["gsc_time"] = float(w[2])

    intf = {}
    cntr = start_cntr
    while True:
        s = parse_interfering(path, l, cntr)
        if s == None:
            break
        intf[cntr] = s
        cntr += 1
    sample["interferers"] = intf
    return sample

def read_input():
    try:
        f = file(cache, "r")
        s = cPickle.load(f)
        f.close()
        return s
    except:
        pass
    series = {}
    for alpha in [100, 75, 50, 40, 30, 20, 10]:
        nr_timeouts = 0
        base = {}
        deltas = {}
        for logfile in os.listdir("%d" % alpha):
            w = logfile.split(".")
            path = "%d/%s" % (alpha, logfile)
            l = file(path)
            if w[-1] == "slog":
                sample = parse_crashing(path, l, int(w[1]))
                assert not deltas.has_key((w[0],w[1]))
                deltas[(w[0],w[1])] = sample
            else:
                sample = parse_crashing(path, l)
                assert not base.has_key(w[0])
                base[w[0]] = sample
            l.close()
        for ((dynrip, _ign), sample) in deltas.iteritems():
            assert base.has_key(dynrip)
            b = base[dynrip]
            assert b.has_key("interferers")
            assert sample.has_key("interferers")
            bi = b["interferers"]
            si = sample["interferers"]
            for (i_key, i_data) in si.iteritems():
                assert bi.has_key(i_key)
                bi[i_key] = i_data

        try:
            p = os.listdir("nr/%d" % alpha)
        except:
            sys.stderr.write("Missing non-repeat data for alpha=%d; skipping.\n" % alpha)
            p = None
        if p == None:
            nr = None
        else:
            nr = []
            for logfile in p:
                path = "nr/%d/%s" % (alpha, logfile)
                l = file(path)
                sample = parse_crashing(path, l)
                nr.append(sample)
        series[alpha] = (base.values(), nr)

    f = file(cache, "w")
    cPickle.dump(series, f)
    f.close()

    return series

def get_quantile(data, quant):
    idx = len(data) * quant
    idx_low = int(idx)
    idx_high = idx_low + 1
    if idx_low < 0:
        return data[0]
    if idx_high >= len(data):
        return data[-1]
    return data[idx_low] + (data[idx_high] - data[idx_low]) * (idx - idx_low)

def _draw_box_plot(x_coord, y_scaler, mini, maxi, p10, p25, p50, p75, p90, (mean, sd, mean2, mean2a, mean2b)):
    print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord, y_scaler(mini),
                                              x_coord, y_scaler(p25))
    print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord, y_scaler(p75),
                                              x_coord, y_scaler(maxi))
    x1 = x_coord - box_width / 2
    x2 = x_coord + box_width / 2
    print "  \\draw [fill,color=black!10] (%f, %f) rectangle (%f, %f);" % (x1, y_scaler(p10),
                                                                           x2, y_scaler(p90))
    print "  \\draw [fill,color=black!50] (%f, %f) rectangle (%f, %f);" % (x1, y_scaler(p25),
                                                                           x2, y_scaler(p75))
    print "  \\draw (%f, %f) -- (%f, %f);" % (x1, y_scaler(p50), x2, y_scaler(p50))

    # Arithmetic mean
    m = y_scaler(mean)
    print "  \\draw (%f, %f) -- (%f, %f) -- (%f, %f) -- (%f, %f);" % (x_coord - 0.1, m - 0.1,
                                                                      x_coord - 0.1, m + 0.1,
                                                                      x_coord + 0.1, m,
                                                                      x_coord - 0.1, m - 0.1)
    top_whisk = y_scaler(mean - sd)
    bottom_whisk = y_scaler(mean + sd)
    print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord - 0.05, top_whisk, x_coord + 0.05, top_whisk)
    print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord, top_whisk, x_coord, m - 0.05)
    print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord - 0.05, bottom_whisk, x_coord + 0.05, bottom_whisk)
    print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord, bottom_whisk, x_coord, m + 0.05)

    if mean2 != None:
        # Geometric/log mean
        m2 = y_scaler(mean2)
        print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord - 0.1, m2 - 0.1,
                                                  x_coord + 0.1, m2 + 0.1)
        print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord - 0.1, m2 + 0.1,
                                                  x_coord + 0.1, m2 - 0.1)
        top_whisk = y_scaler(mean2a)
        bottom_whisk = y_scaler(mean2b)
        print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord - 0.05, top_whisk, x_coord + 0.05, top_whisk)
        print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord, top_whisk, x_coord, m2)
        print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord - 0.05, bottom_whisk, x_coord + 0.05, bottom_whisk)
        print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord, bottom_whisk, x_coord, m2)

def draw_box_plot(x_coord, y_scaler, data, mean):
    data.sort()
    _draw_box_plot(x_coord, y_scaler, min(data), max(data), get_quantile(data, .10),
                   get_quantile(data, 0.25), get_quantile(data, 0.50),
                   get_quantile(data, 0.75), get_quantile(data, 0.90),
                   mean)

def alpha_to_x(alpha):
    return alpha / 100.0 * figwidth

def preamble():
    print "\\begin{tikzpicture}"
def alpha_axis(series):
    print "  %% X axis"
    print "  \\draw[->] (0,0) -- (%f,0);" % figwidth
    for alpha in series:
        print "  \\node at (%f,0) [below] {%d};" % (alpha_to_x(alpha), alpha)
    def area_for_prob(p):
        return p * box_width * 2
    def len_for_prob(p):
        return area_for_prob(p) ** .5

    prob = 10
    l = len_for_prob(prob / 100.0)
    print "  \\node at (%f,-12pt) [below] {Value of \\gls{alpha}.  \\tikz{\\draw [fill] (0,0) rectangle (%f,%f);} = %d\\%%};" % (figwidth / 2,
                                                                                                                                 l, l, prob)

    
def box_legend(offset, include_geom = True):
    print
    print "  %% Legend"
    fl = figwidth + legendwidth
    def d(idx):
        if include_geom:
            return 0.35 + idx * 0.65 / 6
        else:
            return 0.2 + idx * 0.8 / 6
    if include_geom:
        mean = (0.07, 0.05, 0.21, 0.18, 0.24)
    else:
        mean = (0.07, 0.05, None, None, None)
    _draw_box_plot(figwidth + legendwidth, lambda x: x * figheight + offset,
                   d(0), d(6), d(1), d(2), d(3), d(4), d(5), mean)
    print "  \\node at (%f, %f) [left] {Min};" % (fl - box_width / 2, figheight * d(0) + offset)
    print "  \\node at (%f, %f) [left] {Max};" % (fl - box_width / 2, figheight * d(6) + offset)
    print "  \\node at (%f, %f) [left] {10\\%%};" % (fl - box_width / 2, figheight * d(1) + offset)
    print "  \\node at (%f, %f) [left] {25\\%%};" % (fl - box_width / 2, figheight * d(2) + offset)
    print "  \\node at (%f, %f) [left] {Median};" % (fl - box_width / 2, figheight * d(3) + offset)
    print "  \\node at (%f, %f) [left] {75\\%%};" % (fl - box_width / 2, figheight * d(4) + offset)
    print "  \\node at (%f, %f) [left] {90\\%%};" % (fl - box_width / 2, figheight * d(5) + offset)
    print "  \\node at (%f, %f) [left] {\\shortstack[r]{Mean $\\pm_\\mu$ sd\\\\of mean}};" % (fl - box_width / 2, figheight * 0.07 + offset)
    if include_geom:
        print "  \\node at (%f, %f) [left] {\\shortstack[r]{Geometric\\\\mean}};" % (fl - box_width / 2, figheight * 0.21 + offset)

def timeout_chart(y_base, height, max_rate, data, step):
    print
    print "  %% Timeout chart"
    print "  \\draw (0,%f) -- (0, %f);" % (y_base, y_base + height)
    for i in xrange(0,int(100*max_rate) + 1, step):
        print "  \\node at (0,%f) [left] {%d\\%%};" % (y_base + height * i * max_rate / 100, i)
        print "  \\draw [color=black!10] (0,%f) -- (%f,%f);" % (y_base + height * i * max_rate / 100,
                                                                figwidth,
                                                                y_base + height * i * max_rate / 100)
    print "  \\node at (-30pt, %f) [rotate=90, anchor=south] {Timeout rate};" % (y_base + height / 2)
    for (decoration, pts) in data.iteritems():
        print "  \\draw%s (0,%f)" % (decoration, y_base)
        pts.sort()
        for (alpha, val) in pts:
            print "        -- (%f, %f)" % (alpha_to_x(alpha), y_base + height * val * max_rate)
        print "        ;"

def mean(data):
    m = sum(data) / len(data)
    var = sum([(x - m) ** 2 for x in data]) / len(data)
    has_negs = len([x for x in data if x <= 0]) != 0
    if has_negs:
        m2 = None
        m2a = None
        m2b = None
    else:
        d2 = [math.log(x) for x in data]
        m2 = sum(d2) / len(d2)
        sd2 = (sum([(x - m2) ** 2 for x in d2]) / (len(d2) * (len(d2) - 1))) ** .5
        m2a = math.e ** (m2 + sd2)
        m2b = math.e ** (m2 - sd2)
        m2 = math.e ** m2
    return (m, (var / (len(data) - 1)) ** .5, m2, m2a, m2b)

def erf(x):
    # constants
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911

    # Save the sign of x
    sign = 1
    if x < 0:
        sign = -1
    x = abs(x)

    # A&S formula 7.1.26
    t = 1.0/(1.0 + p*x)
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*math.exp(-x*x)

    return sign*y

def gaussian_kernel(bandwidth, location):
    kfnorm = (math.pi * 2) **.5 * bandwidth
    def res(x):
        delta = location - x
        delta /= bandwidth
        return (math.e ** (-0.5 * delta**2)) / kfnorm
    return res
def truncated_gaussian(upper_bound):
    def res(bandwidth, location):
        underlying = gaussian_kernel(bandwidth, location)
        scale = (1 + erf( (upper_bound - location) / (bandwidth * math.sqrt(2)))) / 2
        def r(x):
            if x > upper_bound:
                return 0
            return underlying(x) / scale
        return r
    return res
def guess_bandwidth(pts):
    mean = sum(pts) / len(pts)
    sd = (sum([ (x - mean)**2 for x in pts]) / len(pts))**.5
    return sd / (len(pts) ** .2)
def density_estimator(pts, kernel, bandwidth):
    kernels = [kernel(bandwidth, d) for d in pts]
    def res(k):
        return sum([kernel(k) for kernel in kernels]) / len(kernels)
    return res

height_pre_dismiss_box = 0.5
height_pre_failure_box = 0.5
height_post_timeout_box = 0.5
height_post_oom_box = 0.5
maxtime = 600
def _augment(series):
    if series == None:
        return
    series["tot_samples"] = float(len(series["times"]))
    for k in ["nr_pre_dismiss", "nr_pre_failure", "nr_post_timeout", "nr_post_oom"]:
        if series[k] != None:
            series["tot_samples"] += series[k]
    series["frac_in_data"] = len(series["times"]) / series["tot_samples"]
    ldata = [math.log(d / mintime) for d in series["times"]]
    #kernel = truncated_gaussian(math.log(maxtime/mintime))
    kernel = gaussian_kernel
    bw = guess_bandwidth(ldata)
    series["density"] = density_estimator(ldata, kernel, bw)
    series["bandwidth"] = bw
def pct_label(pct):
    label = "%.0f\\%%" % (round(pct * 100, 0))
    if label == "0\\%":
        label = "$<\!\!\!1$\\%"
    return label

def kde_chart(offset, x_coord, parse_series, data):
    with_repeats = parse_series(data[0])
    without_repeats = parse_series(data[1])
    _augment(with_repeats)
    _augment(without_repeats)

    # Y-extent of the actual density plot part of the graph.
    base_y = offset
    chart_top = offset + figheight

    # Bootstrap for confidence interval
    alts = []
    for i in xrange(0, 10):
        alt = []
        for i in xrange(len(data[0])):
            alt.append(random.choice(data[0]))
        s = parse_series(alt)
        _augment(s)
        alts.append(s)
    def density_sd(y):
        m = math.log(y_to_time(y) / mintime)
        samples = [alt["density"](m) for alt in alts]
        m = sum(samples) / len(samples)
        sd = (sum([(x - m) ** 2 for x in samples]) / len(samples)) **.5
        return sd
    def rate_sd(key):
        samples = [alt[key]/alt["tot_samples"] for alt in alts]
        m = sum(samples) / len(samples)
        sd = (sum([(x - m) ** 2 for x in samples]) / len(samples)) ** .5
        return sd

    # Draw the box parts
    def limmed_rectangle(key, y0, height):
        y1 = y0 + height

        # Do the with-sd version first
        pct = with_repeats[key] / with_repeats["tot_samples"]
        pct_sd = pct + rate_sd(key)
        width = pct_sd / height
        x0 = x_coord - width * box_width
        x1 = x_coord + width * box_width
        if width != 0:
            print "  \\draw [fill,color=blue!50] (%f, %f) rectangle (%f, %f);" % (x0, y0,
                                                                                  x1, y1)
        # Now the without-sd one.
        width = pct / height
        x0 = x_coord - width * box_width
        x1 = x_coord + width * box_width
        if width != 0:
            print "  \\draw [fill] (%f, %f) rectangle (%f, %f);" % (x0, y0,
                                                                    x1, y1)
            label = pct_label(pct)
            print "  \\node at (%f, %f) {%s};" % (x_coord, (y0 + y1) / 2, label)
            print "  \\begin{scope}[white]"
            print "    \\path[clip] (%f, %f) -- (%f, %f) -- (%f, %f) -- (%f, %f);" % (x0, y0,
                                                                                      x1, y0,
                                                                                      x1, y1,
                                                                                      x0, y1)
            print "    \\node at (%f, %f) {%s};" % (x_coord, (y0 + y1) / 2, label)
            print "  \\end{scope}"
            area = width * box_width * 2 * (y1 - y0)
            sys.stderr.write("Box for %f -> width %f, height %f, area %f; tot area %f\n" % (pct, width * box_width * 2,
                                                                                            y1 - y0, area, area / pct))
        if without_repeats != None:
            pct = without_repeats[key] / without_repeats["tot_samples"]
            width = pct / height
            x0 = x_coord - width * box_width
            x1 = x_coord + width * box_width
            if width != 0:
                print "  \\draw [dashed,color=black!50] (%f, %f) rectangle (%f, %f);" % (x0, y0, x1, y1)
    if with_repeats["nr_pre_dismiss"] != None:
        limmed_rectangle("nr_pre_dismiss", base_y, height_pre_dismiss_box)
        base_y += height_pre_dismiss_box
        chart_top -= height_pre_dismiss_box
    if with_repeats["nr_pre_failure"] != None:
        limmed_rectangle("nr_pre_failure", base_y, height_pre_failure_box)
        base_y += height_pre_failure_box
        chart_top -= height_pre_failure_box
    if with_repeats["nr_post_oom"] != None:
        chart_top -= height_post_oom_box
        limmed_rectangle("nr_post_oom", chart_top, height_post_oom_box)
    if with_repeats["nr_post_timeout"] != None:
        chart_top -= height_post_timeout_box
        limmed_rectangle("nr_post_timeout", chart_top, height_post_timeout_box)

    alpha = (chart_top - base_y) / (math.log(maxtime / mintime))
    def time_to_y(t):
        return alpha * math.log(t / mintime) + base_y
    def y_to_time(y):
        return (math.e ** ((y - base_y) / alpha)) * mintime
    def density_at_y(series, y):
        return series["density"](math.log(y_to_time(y) / mintime))

    points_per_cm = 100.0

    # Sanity check: is the area about right?  Fail out if we've lost
    # or gained more than 1%
    area = 0
    area_below = 0
    area_above = 0
    _x = base_y - 5
    while _x < chart_top + 5:
        _x += 1 / points_per_cm
        d = density_at_y(with_repeats, _x)
        if _x < base_y:
            area_below += d
        elif _x <= chart_top:
            area += d
        else:
            area_above += d
    del _x
    area = area / (alpha * points_per_cm)
    area_below = area_below / (alpha * points_per_cm)
    area_above = area_above / (alpha * points_per_cm)
    if abs(area - 1) > 0.01:
        sys.stderr.write("Excessive defect in data; area should be 1, is %f\n" % area)
    area_cm2 = area * box_width * 2 * with_repeats["frac_in_data"]
    sys.stderr.write("Area %f, above %f, below %f (%f cm^2 for %f; total area %f cm^2)\n" % (area, area_above, area_below,
                                                                                             area_cm2,
                                                                                             with_repeats["frac_in_data"],
                                                                                             area_cm2 / with_repeats["frac_in_data"]))
    del area


    # Now calculate the points.
    def calc_points(series):
        mode = None
        y = base_y
        densities = []
        while y < chart_top:
            d = density_at_y(series, y)
            densities.append((y, d))
            if mode == None or d > mode[1]:
                mode = (y, d)
            y += 1/points_per_cm
        series["mode"] = mode[0]
        series["densities"] = densities
    mode = calc_points(with_repeats)
    if without_repeats != None:
        calc_points(without_repeats)
    def draw_plot(series, cmd):
        print "  %s" % cmd,
        d = series["densities"]
        frac_in_data = series["frac_in_data"]
        scale = box_width * frac_in_data / alpha
        for i in xrange(len(d)):
            if i != 0:
                print "        -- ",
            p = d[i]
            print "(%f, %f)" % (x_coord - p[1] * scale, p[0])
        for i in xrange(len(d)):
            p = d[-i - 1]
            print "        -- (%f, %f)" % (x_coord + p[1] * scale, p[0])
        print "        ;"

    # Limm with SD
    with_sd = {"densities": [(y, d + density_sd(y)) for (y, d) in with_repeats["densities"]],
               "frac_in_data": with_repeats["frac_in_data"]}
    draw_plot(with_sd, "\\draw[fill,color=blue!50]")

    # Plot itself
    draw_plot(with_repeats, "\\draw[fill]")
    # Bandwidth indicator
    print "  \\draw (%f, %f) -- (%f, %f);" % (x_coord + .3, time_to_y(mintime),
                                              x_coord + .3, time_to_y(mintime * math.e ** with_repeats["bandwidth"]))

    # Plot without repeats
    if without_repeats != None:
        draw_plot(without_repeats, "\\draw[dashed,color=black!50]")

    # Label.
    mode = with_repeats["mode"]
    print "  \\node at (%f, %f) {%s};" % (x_coord, mode, pct_label(with_repeats["frac_in_data"]))
    print "  \\begin{scope}[white]"
    draw_plot(with_repeats, "  \\path[clip]")
    print "    \\node at (%f,%f) {%s};" % (x_coord, mode, pct_label(with_repeats["frac_in_data"]))
    print "  \\end{scope}"

    # Put in the mean and sd of mean
    data = with_repeats["times"]
    mean = sum(data) / len(data)
    sd = (sum([ (x - mean)**2 for x in data]) / (len(data) * (len(data) - 1)))**.5
    print "  \\draw [color=black!50] (%f,%f) -- (%f, %f);" % (x_coord - .25,
                                                              time_to_y(mean),
                                                              x_coord + .25,
                                                              time_to_y(mean))
    print "  \\draw [color=black!50] (%f, %f) rectangle (%f, %f);" % (x_coord - .25,
                                                                      time_to_y(mean - sd),
                                                                      x_coord + .25,
                                                                      time_to_y(mean + sd))

def kde_axis(offset, include_pre_dismiss, include_pre_failure,
             include_post_oom, include_post_timeout):
    print "  %% KDE axis"
    base_y = 0
    if include_pre_dismiss:
        print "  \\node at (0, %f) [left] {Pre-dismissed};" % (height_pre_dismiss_box / 2 + offset)
        base_y += height_pre_dismiss_box
    if include_pre_failure:
        print "  \\node at (0, %f) [left] {Pre-failed};" % (base_y + height_pre_failure_box / 2 + offset)
        base_y += height_pre_failure_box
    tot_height = figheight - base_y
    if include_post_oom:
        print "  \\node at (0, %f) [left] {Out of memory};" % (tot_height - height_post_oom_box / 2 + offset)
        tot_height -= height_post_oom_box
    if include_post_timeout:
        print "  \\node at (0, %f) [left] {Timeout};" % (tot_height - height_post_timeout_box / 2 + offset)
        tot_height -= height_post_timeout_box

    alpha = (tot_height - base_y) / (math.log(maxtime / mintime))
    def time_to_y(t):
        return alpha * math.log(t / mintime) + base_y
    def y_to_time(y):
        return (math.e ** ((y - base_y) / alpha)) * mintime

    sys.stderr.write("alpha %f, tot_height %f, base_y %f\n" % (alpha, tot_height, base_y))
    sys.stderr.write("mintime %f -> %f, maxtime %f -> %f\n" % (mintime, time_to_y(mintime),
                                                               maxtime, time_to_y(maxtime)))
    print "  \\draw (0,%f) -- (0, %f);" % (base_y + offset, offset + tot_height)
    for k in ["0.0001", "0.001", "0.01", "0.1", "1", "10", "100", "300"]:
        if float(k) >= mintime:
            print "  \\node at (0, %f) [left] {%s};" % (time_to_y(float(k)) + offset, k)
            print "  \\draw [color=black!10] (0,%f) -- (%f, %f);" % (time_to_y(float(k)) + offset, figwidth, time_to_y(float(k)) + offset)
