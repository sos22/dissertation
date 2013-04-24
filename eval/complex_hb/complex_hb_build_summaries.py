#! /usr/bin/env python

import sys
import math
import os
import re
import random

import common

maxtime = 1000.0
mintime = 0.001
regression_threshold1 = 0
regression_threshold2 = 40

def time_to_y(t):
    if t > maxtime:
        return common.fig_height
    if t < mintime:
        return 0
    #math.log(t / mintime) / math.log(maxtime/mintime) * common.fig_height
    return (t - mintime) / (maxtime - mintime) * common.fig_height

def mean_sd(vals):
    mean = sum(vals) / len(vals)
    sd = (sum([(x - mean)**2 for x in vals]) / len(vals)) ** .5
    return (mean, sd)
data = common.load_data(re.compile(r"complex_hb_([0-9]*)\.build_summary_time"))
pts = [(x[0], x[1][0], x[1][1]) for x in data.iteritems() if x[0] < regression_threshold2 and x[0] > regression_threshold1]
common.preamble()
common.x_axis()
common.y_axis(["0", "20", "40", "60", "80", "100", "120", "140", "160", "180", "200", "300", "310", "320", "330", "340", "350", "370", "380", "400"], time_to_y)
common.plot_data(time_to_y, data)

from numpy import matrix
def quartic_regression(pts):
    def regression_basis(x):
        return [1, x, x**2, x**3, x**4]
    x_matrix = matrix([regression_basis(x) for (x,_y,_sd) in pts])
    y_matrix = matrix([[y] for (_x,y,_sd) in pts])
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

predict = quartic_regression(pts)[-1]
print "  \\draw[dotted] ",
first = True
for x in xrange(3, 100):
    p = predict(x)
    if not first:
        print "        -- ",
    first = False
    print "(%f,%f)" % (common.count_to_x(x), time_to_y(p))
print "        ;"

def exponential_regression(pts):
    # Exponential regression to form y = alpha * e ** (beta * x) + gamma.
    # Have to do this one numerically.
    def predict(alpha, beta, gamma, x):
        return alpha * math.e ** (beta * x) + gamma
    def defect(alpha, beta, gamma):
        return sum([((predict(alpha, beta, gamma, x) - y)/1) ** 2 for (x,y,sd) in pts])
    sum_data = sum([y for (_x, y, _sd) in pts])
    def alpha_gamma(beta):
        sum_eb = sum([math.e ** (beta * x) for (x,_y,_sd) in pts])
        sum_yeb = sum([y * math.e ** (beta * x) for (x,y,_sd) in pts])
        sum_2eb = sum([math.e ** (2 * beta * x) for (x,_y,_sd) in pts])
        n = len(data)
        alpha = (n * sum_yeb - sum_data * sum_eb) / (n * sum_2eb - sum_eb * sum_eb)
        gamma = (sum_data - alpha * sum_eb) / n
        return (alpha, gamma)

    # Lacking any better ideas for where to start.
    beta = 1

    (alpha, gamma) = alpha_gamma(beta)
    current_defect = defect(alpha, beta, gamma)
    ratio = 1.5
    for _ in xrange(1000):
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

(alpha, beta, gamma, predict) = exponential_regression(pts)

sys.stderr.write("import math\n")
sys.stderr.write("def exp_predictor(x):\n")
sys.stderr.write("    return %f * math.e ** (%f * x) + %f\n\n" % (alpha, beta, gamma))

print "  \\draw ",
first = True
for x in xrange(3, 100):
    p = predict(x)
    if not first:
        print "        -- ",
    first = False
    print "(%f,%f)" % (common.count_to_x(x), time_to_y(p))
print "        ;"

# Do a bootstrap
# def resample():
#     return [random.choice(pts) for _ in pts]
# def bootstrap(regression_fn, labels):
#     samples = [regression_fn(resample()) for _ in xrange(10000)]
#     p = [mean_sd([x[i] for x in samples]) for i in xrange(len(labels))]
#     sys.stderr.write(", ".join(["%s = %e +- %e" % (labels[i], p[i][0], p[i][1]) for i in xrange(len(labels))]) + "\n")
# bootstrap(exponential_regression, ["alpha", "beta", "gamma"])
# bootstrap(quartic_regression, ["0", "1", "2", "3", "4"])

common.postamble()
