import sys
import os
import math
import cPickle

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
    if line in ["Child failed in run_in_child, signal 11", "OOM kill in checkWhetherInstructionCanCrash()"]:
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
        sample["gsc_timed_out"] = True
        return sample
    w = line.split()
    if len(w) != 3 or w[0] != "atomicSurvivalConstraint" or w[1] != "took":
        fail("%s lacks an ASC line (%s)" % (path, line))
    sample["asc_time"] = float(w[2])

    line = l.readline().strip()
    if line == "Child timed out in run_in_child":
        sample["gsc_timed_out"] = True
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
        series[alpha] = base.values()

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
        return p * box_width
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

height_pre_dismiss_box = 0.5
height_pre_failure_box = 0.5
height_post_timeout_box = 0.5
height_post_oom_box = 0.5
maxtime = 300
def kde_chart(offset, x_coord, nr_pre_dismiss, nr_pre_failure, data, nr_post_timeout, nr_post_oom,
              limm):
    if limm:
        decoration = "color=black!50,dotted"
    else:
        decoration = "fill"
    tot_samples = float(len(data))
    if nr_pre_dismiss != None:
        tot_samples += nr_pre_dismiss
    if nr_pre_failure != None:
        tot_samples += nr_pre_failure
    if nr_post_timeout != None:
        tot_samples += nr_post_timeout
    if nr_post_oom != None:
        tot_samples += nr_post_oom
    frac_in_data = len(data) / tot_samples

    ldata = map(math.log, data)
    mean = sum(ldata) / len(ldata)
    sd = (sum([ (x - mean)**2 for x in ldata]) / len(ldata))**.5
    bandwidth = sd / (len(ldata) ** .2)

    area = 0
    base_y = 0

    def limmed_rectangle(width, y0, y1):
        if width == 0:
            return
        print "  \\draw [%s] (%f, %f) rectangle (%f, %f);" % (decoration,
                                                              x_coord - width * box_width,
                                                              offset + y0,
                                                              x_coord + width * box_width,
                                                              offset + y1)

    # Draw the box parts
    if nr_pre_dismiss != None:
        density_pre_dismiss = nr_pre_dismiss / (tot_samples * height_pre_dismiss_box)
        limmed_rectangle(density_pre_dismiss, base_y, base_y + height_pre_dismiss_box)
        base_y += height_pre_dismiss_box
        area += density_pre_dismiss * 2 * box_width * height_pre_dismiss_box
        sys.stderr.write("nr_pre_dismiss %d/%d -> area %f = %f * 2 * %f * %f\n" % (nr_pre_dismiss, tot_samples, area, density_pre_dismiss, box_width, height_pre_dismiss_box))
    if nr_pre_failure != None:
        density_pre_failure = nr_pre_failure / (tot_samples * height_pre_failure_box)
        limmed_rectangle(density_pre_failure, base_y, base_y + height_pre_failure_box)
        base_y += height_pre_failure_box
        area += density_pre_failure * 2 * box_width * height_pre_failure_box
    tot_height = figheight - base_y
    if nr_post_oom != None:
        density_post_oom = nr_post_oom / (tot_samples * height_post_oom_box)
        tot_height -= height_post_oom_box
        limmed_rectangle(density_post_oom, tot_height, tot_height + height_post_oom_box)
        area += density_post_oom * 2 * box_width * height_post_oom_box
    if nr_post_timeout != None:
        density_post_timeout = nr_post_timeout / (tot_samples * height_post_timeout_box)
        tot_height -= height_post_timeout_box
        limmed_rectangle(density_post_timeout, tot_height, tot_height + height_post_timeout_box)
        area += density_post_timeout * 2 * box_width * height_post_timeout_box


    # Scale will be y = alpha log(t) + beta
    alpha = (tot_height - base_y) / (math.log(maxtime) - math.log(mintime))
    beta = base_y -alpha * math.log(mintime)

    _kfnorm = (math.pi * 2) **.5
    def kernel_function(bandwidth, delta):
        delta /= bandwidth
        return (math.e ** (-0.5 * delta**2)) / (_kfnorm * bandwidth)
    def density_at(val):
        return sum([kernel_function(bandwidth, d - val) for d in ldata]) * frac_in_data / len(ldata)

    sys.stderr.write("Kernel bandwidth %e\n" % bandwidth)
    #_acc = 0
    #_foox = -10
    #while _foox < 10:
    #    _acc += kernel_function(bandwidth, _foox)
    #    _foox += 0.00001
    #sys.stderr.write("Kernel function -> %f\n" % (_acc * 0.00001))

    points_per_cm = 100.0

    # Sanity check: is the area about right?
    main_area = 0
    y = base_y
    while y < tot_height:
        time = math.e ** ( (y - base_y - beta) / alpha )
        d = density_at(math.log(time))
        main_area += d / (points_per_cm * alpha)
        y += 1 / points_per_cm
    main_area *= box_width * 2
    sys.stderr.write("alpha = %f, Area: %f + %f = %f, frac_in_data = %f\n" % (alpha, area, main_area, area + main_area, frac_in_data))

    # Now do the actual density plot
    print "  \\draw [%s] " % decoration,
    isFirst = True
    y = base_y
    while y < tot_height:
        # Convert y to time
        time = math.e ** ( (y - base_y - beta) / alpha )
        # Get the density
        d = density_at(math.log(time))
        # Actually put in the point
        if not isFirst:
            print "        -- ",
        isFirst = False
        print "(%f,%f) %%%% %f" % (x_coord - d * box_width, y + offset, time)
        # Move on to next point
        y += 1 / points_per_cm
    # And back down the other side
    while y > base_y:
        time = math.e ** ( (y - base_y - beta) / alpha )
        d = density_at(math.log(time))
        print "        -- (%f,%f) %%%% %f" % (x_coord + d * box_width, y + offset, time)
        y -= 1 / points_per_cm
    # Done
    print "        ;"

    if limm:
        def time_to_y(time):
            return alpha * math.log(time) + beta

        # Put in the mean and sd of mean
        mean = sum(data) / len(data)
        sd = (sum([ (x - mean)**2 for x in data]) / (len(data) * (len(data) - 1)))**.5
        print "  \\draw [color=black!50] (%f,%f) -- (%f, %f);" % (x_coord - box_width,
                                                                  time_to_y(mean) + offset,
                                                                  x_coord + box_width,
                                                                  time_to_y(mean) + offset)
        print "  \\draw [color=black!50] (%f, %f) rectangle (%f, %f);" % (x_coord - box_width,
                                                                          time_to_y(mean - sd) + offset,
                                                                          x_coord + box_width,
                                                                          time_to_y(mean + sd) + offset)
    
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

    # Scale will be y = alpha log(t) + beta
    alpha = (tot_height - base_y) / (math.log(maxtime) - math.log(mintime))
    beta = base_y - alpha * math.log(mintime)
    def time_to_y(time):
        return alpha * math.log(time) + beta

    sys.stderr.write("alpha %f, beta %f, tot_height %f, base_y %f\n" % (alpha, beta, tot_height, base_y))
                     
    print "  \\draw (0,%f) -- (0, %f);" % (base_y + offset, offset + tot_height)
    for k in ["0.001", "0.01", "0.1", "1", "10", "100", "300"]:
        if float(k) >= mintime:
            print "  \\node at (0, %f) [left] {%s};" % (time_to_y(float(k)) + offset, k)
            print "  \\draw [color=black!10] (0,%f) -- (%f, %f);" % (time_to_y(float(k)) + offset, figwidth, time_to_y(float(k)) + offset)
