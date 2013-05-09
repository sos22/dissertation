#! /usr/bin/env python

import sys
import math
import os
import re
import random

import common

maxtime = 2000.0
mintime = 0.001
regression_threshold1 = 0
regression_threshold2 = 40
nr_replicates = 1000

def get_quantile(data, q):
    idx = q * len(data)
    idx1 = int(idx)
    idx2 = idx1 + 1
    if idx2 >= len(data):
        return data[-1]
    return data[idx1] * (idx - idx1) + data[idx2] * (1 - idx + idx1)

def time_to_y(t):
    if t > maxtime:
        return common.fig_height
    if t < mintime:
        return 0
    return math.log(t / mintime) / math.log(maxtime/mintime) * common.fig_height
    #return (t - mintime) / (maxtime - mintime) * common.fig_height

data = common.load_data(re.compile(r"complex_hb_([0-9]*)\.build_summary_time"))

abscissae = [13, 17, 21, 23, 25, 29, 3, 33, 37, 41, 43, 45, 49, 5, 53, 63, 65, 69, 73, 77, 79, 9]
abscissae.sort()
#data = {}
#for k in abscissae:
#    data[k] = [1.01 ** k + random.gauss(0, 0.0001) for _ in xrange(10)]
#    #data[k] = [0.5 + 0.04 * k + 0.003 * k ** 2 + 0.0002 * k ** 3 + 0.00001 * k ** 4 + random.gauss(0, 5) for _ in xrange(10)]

common.preamble()
common.x_axis()
common.y_axis(["0.1", "1", "2", "4", "10", "20", "40", "80", "150", "300"], time_to_y)

from numpy import matrix
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

# Bootstrap a confidence interval
def gen_replicate(data):
    d = {}
    for (k, v) in data.iteritems():
        d[k] = [random.choice(v) for _ in xrange(len(v))]
    return d
replicates = [quartic_regression(gen_replicate(data))[-1] for _ in xrange(nr_replicates)]
def bootstrap_confidence_interval(x, interval, replicates):
    samples = [r(x) for r in replicates]
    samples.sort()
    return (get_quantile(samples, (1 - interval) / 2),
            get_quantile(samples, (1 + interval) / 2))

bs_interval = {}
for abs in xrange(0,101,1):
    bs_interval[abs] = bootstrap_confidence_interval(abs, .9, replicates)
q = bs_interval[0]
print "  \\fill [color=black!50] (%f, %f) -- (%f, %f)" % (common.count_to_x(0), time_to_y(q[0]),
                                                          common.count_to_x(0), time_to_y(q[1]))
for a in xrange(5,101,5):
    print "        -- (%f, %f)" % (common.count_to_x(a), time_to_y(bs_interval[a][1]))
for a in reversed(xrange(5, 101,5)):
    print "        -- (%f, %f)" % (common.count_to_x(a), time_to_y(bs_interval[a][0]))
print "        -- cycle;"

predict = quartic_regression(data)[-1]
print "  \\draw[dotted] ",
first = True
for x in xrange(3, 100):
    p = predict(x)
    if not first:
        print "        -- ",
    first = False
    print "(%f,%f)" % (common.count_to_x(x), time_to_y(p))
print "        ;"

common.plot_data(time_to_y, data)

def exponential_regression(pts):
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

restrict_data = {}
for (k, v) in data.iteritems():
    if regression_threshold1 <= k <= regression_threshold2:
        restrict_data[k] = v
(alpha, beta, gamma, predict) = exponential_regression(restrict_data)

sys.stderr.write("import math\n")
sys.stderr.write("def exp_predictor(x):\n")
sys.stderr.write("    return %f * math.e ** (%f * x) + %f\n\n" % (alpha, beta, gamma))

replicates = [exponential_regression(gen_replicate(restrict_data))[-1] for _ in xrange(nr_replicates)]
bs_interval = {}
for abs in xrange(0,101):
    bs_interval[abs] = bootstrap_confidence_interval(abs, .9, replicates)
q = bs_interval[0]
print "  \\fill [color=black!50] (%f, %f) -- (%f, %f)" % (common.count_to_x(0), time_to_y(q[0]),
                                                          common.count_to_x(0), time_to_y(q[1]))
for a in xrange(5,101,5):
    print "        -- (%f, %f)" % (common.count_to_x(a), time_to_y(bs_interval[a][1]))
for a in reversed(xrange(5, 101,5)):
    print "        -- (%f, %f)" % (common.count_to_x(a), time_to_y(bs_interval[a][0]))
print "        -- cycle;"

print "  \\draw ",
first = True
for x in xrange(3, 100):
    p = predict(x)
    if not first:
        print "        -- ",
    first = False
    print "(%f,%f)" % (common.count_to_x(x), time_to_y(p))
print "        ;"

# # Do a bootstrap
# nr_replicates = 100
# def resample():
#     d = {}
#     for (k, v) in data.iteritems():
#         d[k] = [random.choice(v) for _ in xrange(nr_replicates)]
#     return d
# exp_regress = 

# def bootstrap(regression_fn, labels):
#     samples = [regression_fn(resample()) for _ in xrange(10000)]
#     p = [mean_sd([x[i] for x in samples]) for i in xrange(len(labels))]
#     sys.stderr.write(", ".join(["%s = %e +- %e" % (labels[i], p[i][0], p[i][1]) for i in xrange(len(labels))]) + "\n")
# bootstrap(exponential_regression, ["alpha", "beta", "gamma"])
# bootstrap(quartic_regression, ["0", "1", "2", "3", "4"])

common.postamble()
