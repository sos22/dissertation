#! /usr/bin/env python

import math
import random
from numpy import matrix

fig_height = 6.8
fig_width = 13.3
maxtime = 600.0
mintime = 0.1
maxmem = 8388608
minmem = 4194304
regression_threshold1 = 7
regression_threshold2 = 20
nr_replicates = 1000
error_bar_width = 0.002
cross_width = error_bar_width
cross_height = cross_width * (fig_width / fig_height)

abscissae = range(0, 41, 2)
def float_range(start, end, step):
    start = float(start)
    end = float(end)
    step = float(step)
    while start < end:
        yield start
        start += step
regression_abs = list(float_range(0,41,.1))

def mean_sd(data):
    m = sum(data) / float(len(data))
    sd = (sum((x - m) ** 2.0 for x in data) / len(data)) ** .5
    return (m, sd)

def get_quantile(data, q):
    idx = q * len(data)
    idx1 = int(idx)
    idx2 = idx1 + 1
    if idx2 >= len(data):
        return data[-1]
    return data[idx1] * (idx - idx1) + data[idx2] * (1 - idx + idx1)

def time_to_y(t):
    if t < 0:
        return 0
    return math.log(t / mintime) / math.log(maxtime/mintime)
    #return (t - mintime) / (maxtime - mintime)
def mem_to_y(m):
    if m < 0:
        return 0
    return math.log(m / minmem) / math.log(maxmem/minmem)

def count_to_x(count):
    return count / 40.0

def quartic_regression(pts):
    def regression_basis(x):
        return [1, x, x**2, x**3, x**4]
    a = list(filter(lambda x: regression_threshold1 <= x < regression_threshold2, pts.iterkeys()))
    x_matrix = matrix([regression_basis(x) for x in a])
    y_matrix = matrix([pts[x] for x in a])
    coeff_matrix = (x_matrix.T * x_matrix).I * x_matrix.T * y_matrix
    regression_coefficients = coeff_matrix.T.tolist()[0]

    def predict(x):
        acc = 0
        basis = regression_basis(x)
        assert len(basis) == len(regression_coefficients)
        for i in xrange(len(basis)):
            acc += basis[i] * regression_coefficients[i]
        return acc
    return (regression_coefficients) + [predict]

def exponential_regression(all_pts):
    pts = {}
    for (k, v) in all_pts.iteritems():
        if regression_threshold1 <= k <= regression_threshold2:
            pts[k] = v
    # Exponential regression to form y = alpha * e ** (beta * x) + gamma.
    # Have to do this one numerically.
    def predict(alpha, beta, gamma, x):
        return alpha * math.e ** (beta * x) + gamma
    def defect(alpha, beta, gamma):
        return sum([(predict(alpha, beta, gamma, x) - y) ** 2 for (x,ys) in pts.iteritems() for y in ys])
    sum_y = sum(sum(y) for y in pts.itervalues())
    n = sum(len(x) for x in pts.itervalues())
    def alpha_gamma(beta):
        sum_eb = sum(math.e ** (beta * x) * len(ys) for (x,ys) in pts.iteritems())
        sum_yeb = sum(y * math.e ** (beta * x) for (x,ys) in pts.iteritems() for y in ys)
        sum_2eb = sum(math.e ** (2 * beta * x) * len(ys) for (x,ys) in pts.iteritems())
        alpha = (n * sum_yeb - sum_y * sum_eb) / (n * sum_2eb - sum_eb * sum_eb)
        gamma = (sum_y - alpha * sum_eb) / n
        return (alpha, gamma)

    # Lacking any better ideas for where to start.
    beta = 1

    (alpha, gamma) = alpha_gamma(beta)
    current_defect = defect(alpha, beta, gamma)
    ratio = 1.1
    for _ in xrange(100):
        beta_high = beta * ratio
        beta_low = beta / ratio
        (alphah, gammah) = alpha_gamma(beta_high)
        defecth = defect(alphah, beta_high, gammah)

        (alphal, gammal) = alpha_gamma(beta_low)
        defectl = defect(alphal, beta_low, gammal)

        if defecth < defectl:
            new_beta = beta_high
            new_alpha = alphah
            new_gamma = gammah
            new_defect = defecth
        else:
            new_beta = beta_low
            new_alpha = alphal
            new_gamma = gammal
            new_defect = defectl
        if current_defect < new_defect:
            ratio = ratio ** .5
        else:
            alpha = new_alpha
            beta = new_beta
            gamma = new_gamma
            current_defect = new_defect
            ratio = ratio ** .99
    return (alpha, beta, gamma, lambda x: predict(alpha, beta, gamma, x))

def gen_replicate(data):
    d = {}
    for (k, v) in data.iteritems():
        d[k] = [random.choice(v) for _ in xrange(len(v))]
    return d

def bootstrap_confidence_interval(x, interval, replicates):
    samples = [r(x) for r in replicates]
    samples.sort()
    return (get_quantile(samples, (1 - interval) / 2),
            get_quantile(samples, (1 + interval) / 2))

times = {}
mems = {}
timeouts = set()
with open("results") as f:
    for l in f.xreadlines():
        w = l.split()
        if w[0] == "Rep":
            continue
        key = (int(w[0]) + 1) / 2
        if times.has_key(key):
            if w[1] == "timeout":
                timeouts.add(key)
            else:
                times[key].append(float(w[2]))
                mems[key].append(int(w[1]))
        else:
            # Discard first result at each count, because that avoids
            # some kinds of initial transient.
            times[key] = []
            assert not mems.has_key(key)
            mems[key] = []

#data = {}
#for k in abscissae:
#    data[k] = [1.01 ** k + random.gauss(0, 0.0001) for _ in xrange(10)]
#    #data[k] = [0.5 + 0.04 * k + 0.003 * k ** 2 + 0.0002 * k ** 3 + 0.00001 * k ** 4 + random.gauss(0, 5) for _ in xrange(10)]

def draw_regression(output, regressor, data, decoration, time_to_y):
    output.write("      % Bootstrapped confidence interval\n")
    replicates = [regressor(gen_replicate(data))[-1] for _ in xrange(nr_replicates)]
    bs_interval = {}
    for abs in regression_abs:
        bs_interval[abs] = bootstrap_confidence_interval(abs, .9, replicates)
    q = bs_interval[0]
    output.write("      \\fill [color=black!50] (0, %f) -- (0, %f)\n" % (time_to_y(q[0]), time_to_y(q[1])))
    for a in regression_abs:
        output.write("              -- (%f, %f)\n" % (count_to_x(a), time_to_y(bs_interval[a][1])))
    for a in reversed(regression_abs):
        output.write("              -- (%f, %f)\n" % (count_to_x(a), time_to_y(bs_interval[a][0])))
    output.write("            -- cycle;\n")
    predict = regressor(data)[-1]

    output.write("      % Regression line itself\n")
    output.write("      \\draw%s " % decoration)
    first = True
    for x in regression_abs:
        p = predict(x)
        if not first:
            output.write("              -- ")
        first = False
        output.write("  (%f,%f)\n" % (count_to_x(x), time_to_y(p)))
    output.write("              ;\n\n")

def in_layer(name, what):
    output.write("    \\begin{pgfonlayer}{%s}%s\end{pgfonlayer}\n" % (name, what))

def draw_graph(output, ysteps, data, timeouts, time_to_y):
    output.write("    \\fill [color=white] (0,0) rectangle (1,1);\n")
    output.write("    \\draw (%f,1) -- ++(0,.02) to node [above = -.1] {Regresion training region} (%f,1.02) -- ++(0,-.02);\n" % (count_to_x(regression_threshold1),
                                                                                                                                  count_to_x(regression_threshold2)))
    output.write("    \\fill [color=blue!20] (%f,0) rectangle (%f,1);\n" % (count_to_x(regression_threshold1),
                                                                            count_to_x(regression_threshold2)))

    output.write("    %% X axis\n")
    in_layer("fg", "\\draw[->] (0,0) -- (1,0);")
    for idx in abscissae:
        x = count_to_x(idx)
        output.write("    \\draw [color=black!10] (%f,0) -- (%f,1);\n" % (x, x))
        in_layer("fg","\\path (%f, 0) node [below] {%d};" % (x, idx))
    output.write("    \\path (0.5,-.08) node [below] {$N$};\n\n")

    output.write("    %% Y axis\n")
    in_layer("fg", "\\draw[->] (0,0) -- (0,1);")
    for idx in ysteps:
        y = time_to_y(float(idx))
        output.write("    \\draw [color=black!10] (0,%f) -- (1,%f);\n" % (y, y))
        in_layer("fg", "\\path (0,%f) node [left] {%s};" % (y, idx))
    output.write("    \\path (-.09,.5) node [rotate=90,below] {Time, seconds};\n\n")

    output.write("    %% Regressions\n")
    output.write("    {\n")
    output.write("      \\path [clip] (0,0) rectangle (1,1);\n")
    output.write("      %% Quartic regression\n")
    draw_regression(output, quartic_regression, data, "[dotted]", time_to_y)
    output.write("      %% Exponential regression\n")
    draw_regression(output, exponential_regression, data, "", time_to_y)
    output.write("    }\n")

    output.write("    %% Actual data\n")
    for (k, v) in data.iteritems():
        output.write("    %% count = %d\n" % k)
        x = count_to_x(k)
        if k in timeouts:
            continue
        (mean, sd) = mean_sd(v)
        # Use the SD of mean
        sd /= (len(v) - 1) ** .5
        # Want a two-tailed 90% interval
        sd *= 1.64
        center = time_to_y(mean)
        lower = time_to_y(mean - sd)
        upper = time_to_y(mean + sd)
        output.write("    \\draw (%f,%f) -- (%f,%f);\n" % (x, lower, x, upper))
        output.write("    \\draw (%f,%f) -- (%f,%f);\n" % (x-error_bar_width, lower, x + error_bar_width, lower))
        output.write("    \\draw (%f,%f) -- (%f,%f);\n" % (x-error_bar_width, upper, x + error_bar_width, upper))
        output.write("    \\draw (%f,%f) -- (%f,%f);\n" % (x - cross_width, center - cross_height,
                                                           x + cross_width, center + cross_height))
        output.write("    \\draw (%f,%f) -- (%f,%f);\n" % (x + cross_width, center - cross_height,
                                                           x - cross_width, center + cross_height))

output = file("complex_hb_build_summaries.tex", "w")
output.write("\\begin{tikzpicture}\n")
output.write("  \\begin{scope}[xshift=0,yshift=0,xscale=%f,yscale=%f]\n" % (fig_width, fig_height))
draw_graph(output,
          ["0.1", "0.2", "0.4", "1", "2", "4", "10", "20", "40", "80", "150", "300", "600"],
          times,
          timeouts,
          time_to_y)
output.write("  \\end{scope}\n")
# output.write("  \\begin{scope}[xshift=%f,yshift=0,xscale=%f,yscale=%f]\n" % (fig_width, fig_width, fig_height))
# draw_graph(output,
#            ["0.1", "0.2", "0.5", "1", "2", "4", "10", "20", "40", "80", "150", "300", "600"],
#            mems,
#            timeouts,
#            mem_to_y)
# output.write("  \\end{scope}\n")
output.write("\\end{tikzpicture}\n")
