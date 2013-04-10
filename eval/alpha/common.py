import sys
import os
import math
import cPickle

cache = "data_cache.pkl"

figheight = 10.0
figwidth = 11.0
legendwidth = 2.5
box_width = 0.3

mintime = 0.0001

def fail(msg):
    sys.stderr.write("%s\n" % msg)

def read_input():
    try:
        f = file(cache, "r")
        s = cPickle.load(f)
        f.close()
        return s
    except:
        pass
    series = {}
    for alpha in [10,20,30,40,50,75,100]:
        nr_timeouts = 0
        data = []
        for logfile in os.listdir("%d" % alpha):
            path = "%d/%s" % (alpha, logfile)

            sample = {}
            sample["nr_crashing_instrs"] = None
            sample["initial_crashing_states"] = None
            sample["simplified_crashing_states"] = None
            sample["bpm_time"] = None
            sample["asc_time"] = None
            sample["gsc_time"] = None
            sample["gsc_timed_out"] = None
            sample["nr_store_cfgs"] = None
            sample["interferers"] = None
            data.append(sample)

            l = file(path)
            
            line = l.readline().strip()
            if line == "buildProbeMachine timed out":
                continue
            w = line.split()
            if len(w) != 5 or w[0:3] != ["Crashing", "CFG", "has"] or w[-1] != "instructions":
                fail("%s doesn't start with CChi line (%s)" % (path, line))
            sample["nr_crashing_instrs"] = int(w[3])
            assert int(w[3]) >= 10

            line = l.readline().strip()
            if line == "buildProbeMachine timed out":
                continue
            w = line.split()
            if len(w) != 6 or w[0:4] != ["Initial", "crashing", "machine", "has"] or w[-1] != "states":
                fail("%s missing ICMS line (%s)" % (path, line))
            sample["initial_crashing_states"] = int(w[4])

            line = l.readline().strip()
            if line == "buildProbeMachine timed out":
                continue
            w = line.split()
            if len(w) != 6 or w[0:4] != ["Simplified", "crashing", "machine", "has"] or w[-1] != "states":
                fail("%s missing SCMS line (%s)" % (path, line))
            sample["simplified_crashing_states"] = int(w[4])

            line = l.readline().strip()
            w = line.split()
            if len(w) != 3 or w[0] != "buildProbeMachine" or w[1] != "took":
                fail("%s doesn't start with bpm line (%s)" % (path, line))
            sample["bpm_time"] = float(w[2])

            line = l.readline()
            if line == "":
                l.close()
                continue
            line = line.strip()
            if line in ["no conflicting stores", "No conflicting stores (1951)", "No conflicting stores (1925)"]:
                sample["nr_store_cfgs"] = 0
                sample["gsc_time"] = mintime
                sample["gsc_timed_out"] = False
                continue
            if line in ["atomicSurvivalConstraint timed out", "removeAnnotations timed out", "removeAnnotations timed out (1915)",
                        "removeAnnotations failed"]:
                sample["gsc_timed_out"] = True
                continue
            w = line.split()
            if len(w) != 3 or w[0] != "atomicSurvivalConstraint" or w[1] != "took":
                fail("%s lacks an ASC line (%s)" % (path, line))
            sample["asc_time"] = float(w[2])

            line = l.readline().strip()
            if line == "getStoreCFGs timed out":
                sample["gsc_timed_out"] = True
                continue
            if line == "":
                sample["gsc_timed_out"] = False
                sample["gsc_time"] = mintime
                sample["nr_store_cfgs"] = 0
                continue
            w = line.split()
            if len(w) != 6 or w[0] != "getStoreCFGs" or w[1] != "took" or w[3] != "seconds," or w[4] != "produced":
                fail("%s lacks a GSC line (%s)" % (path, line))
            sample["gsc_timed_out"] = False
            sample["nr_store_cfgs"] = int(w[5])
            sample["gsc_time"] = float(w[2])

            intf = []
            sample["interferers"] = intf
            while True:
                sample = {}
                sample["nr_instrs"] = None
                sample["initial_interfering_states"] = None
                sample["simplified_interfering_states"] = None
                sample["bsm_time"] = None
                sample["gvc_time"] = None
                sample["gvc_timeout"] = None
                sample["generated_vc"] = None

                line = l.readline().strip()
                if line == "":
                    break;
                intf.append(sample)
                w = line.split()[1:]
                if len(w) != 5 or w[:3] != ["Interfering", "CFG", "has"]:
                    fail("%s got bad ich line %s" % (path, line))
                sample["nr_instrs"] = int(w[3])

                line = l.readline().strip()
                w = line.split()[1:]
                if w == ["buildStoreMachine", "timed", "out"]:
                    continue
                if w == ["single", "store", "versus", "single", "shared", "load"]:
                    sample["bsm_time"] = mintime
                    sample["gvc_time"] = mintime
                    sample["gvc_timeout"] = False
                    sample["generated_vc"] = False
                    continue
                if len(w) != 6 or w[:4] != ["Initial", "interfering", "StateMachine", "has"]:
                    fail("%s got bad ich2 line %s" % (path, line))
                sample["initial_interfering_states"] = int(w[4])
                
                line = l.readline().strip()
                w = line.split()[1:]
                if w == ["buildStoreMachine", "timed", "out"]:
                    continue
                if len(w) != 6 or w[:4] != ["Simplified", "interfering", "StateMachine", "has"]:
                    fail("%s got bad ich3 line %s" % (path, line))
                sample["simplified_interfering_states"] = int(w[4])

                line = l.readline().strip()
                w = line.split()[1:]
                if len(w) != 3 or w[:2] != ["buildStoreMachine", "took"]:
                    fail("%s got bad ich4 line %s" % (path, line))
                sample["bsm_time"] = float(w[2])

                line = l.readline().strip()
                w = line.split()[1:]
                if w[:-1] in [["single", "store", "versus", "single", "load,", "after", "localise"],
                              ["generated", "VC"],
                              ["crash", "impossible"],
                              ["IC", "is", "false"]]:
                    t = float(w[-1][1:-1])
                    sample["gvc_time"] = t
                    sample["gvc_timeout"] = False
                    sample["generated_vc"] = w[:-1] == ["generated", "VC"]
                    continue
                if w in [["crash", "timed", "out"],
                         ["IC", "atomic", "timed", "out"],
                         ["rederive", "CI", "atomic", "timed", "out"]]:
                    sample["gvc_timeout"] = True
                    continue
                fail("Huh? %s, %s" % (path, line))

            l.close()
        series[alpha] = data

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
    print "  \\node at (%f,-12pt) [below] {Value of \\gls{alpha}};" % (figwidth / 2)
    
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
        mean = (0.07, 0.05, None, None, None)
    else:
        mean = (0.07, 0.05, 0.17, 0.12, 0.23)
    _draw_box_plot(figwidth + legendwidth, lambda x: x * figheight + offset,
                   d(0), d(6), d(1), d(2), d(3), d(4), d(5), mean)
    print "  \\node at (%f, %f) [left] {Min};" % (fl - box_width / 2, figheight * d(0) + offset)
    print "  \\node at (%f, %f) [left] {Max};" % (fl - box_width / 2, figheight * d(6) + offset)
    print "  \\node at (%f, %f) [left] {10\\%%};" % (fl - box_width / 2, figheight * d(1) + offset)
    print "  \\node at (%f, %f) [left] {25\\%%};" % (fl - box_width / 2, figheight * d(2) + offset)
    print "  \\node at (%f, %f) [left] {Median};" % (fl - box_width / 2, figheight * d(3) + offset)
    print "  \\node at (%f, %f) [left] {75\\%%};" % (fl - box_width / 2, figheight * d(4) + offset)
    print "  \\node at (%f, %f) [left] {90\\%%};" % (fl - box_width / 2, figheight * d(5) + offset)
    print "  \\node at (%f, %f) [left] {\\shortstack[r]{Mean $\\pm$ sd\\\\of mean}};" % (fl - box_width / 2, figheight * 0.07 + offset)
    if include_geom:
        print "  \\node at (%f, %f) [left] {\\shortstack[r]{Geometric\\\\mean}};" % (fl - box_width / 2, figheight * 0.12 + offset)

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
