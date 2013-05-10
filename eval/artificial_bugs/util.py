import math

fig_width = 6.0
max_time = 180
abscissae = [0.1,0.5,1,2,4,8,16,32,64,180]

decorations = ["", "[dashed]", "[dotted]","[color=black!50]"]
def fail(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)

def render_nr(t):
    if t == 0:
        return "0"
    nr_digits = int(math.log(t) / math.log(10))
    natural_max = float(10 ** nr_digits)
    first_digit = int(t/natural_max)
    if nr_digits < -4 or nr_digits > 4:
        return "$%d {\\times} 10^{%d}$" % (first_digit, nr_digits)
    elif nr_digits >= 0:
        return ("%d" % first_digit) + "0" * nr_digits
    else:
        return "0." + ("0" * (-nr_digits - 1)) + ("%d" % first_digit)

def round_up(t):
    nr_digits = int(math.log(t) / math.log(10)) + 1
    natural_max = float(10 ** nr_digits)
    if t / natural_max > 0.8:
        return (natural_max, natural_max / 10)
    first_digit = int(10 * t/natural_max) + 1
    return (first_digit * float(10 ** (nr_digits - 1)), natural_max/10)

def perc_to_y(p):
    return (p * 5.0)
def time_to_x(t):
    return math.log(t/0.1) * fig_width / math.log(max_time * 10)

def read_series(fname):
    f = file(fname, "r")
    nr_timeouts = 0
    times = []
    for l in f:
        if l.strip()[-1] == "T":
            nr_timeouts += 1
        else:
            times.append(float(l.strip()))
    times.sort()
    t = []
    for i in xrange(len(times)):
        t.append( (times[i], float(i)/(len(times) + nr_timeouts - 1)) )
    return (t, nr_timeouts)

def plot_errors(data):
    dkw_bound = (-math.log(0.9/2) / (2.0 * len(data))) ** .5
    # Error region first
    print "  \\fill [color=black!50] (0,0) -- (0, %f)" % (perc_to_y(dkw_bound))
    for (x, y) in data:
        if x < 0.1:
            x = 0.1
        y2 = y + dkw_bound
        if y2 > 1:
            y2 = 1
        print "        -- (%f, %f)" % (time_to_x(x), perc_to_y(y2))
    print "        -- (%f, %f) -- (%f, %f) -- (%f, %f)" % (fig_width, perc_to_y(1.0),
                                                           fig_width, perc_to_y(1.0 - dkw_bound),
                                                           time_to_x(data[-1][0]),
                                                           perc_to_y(1.0 - dkw_bound))
    for (x, y) in reversed(data):
        if x < 0.1:
            x = 0.1
        y2 = y - dkw_bound
        if y2 < 0:
            y2 = 0
        print "        -- (%f, %f)" % (time_to_x(x), perc_to_y(y2))
    print "        -- cycle;"
    
def plot_series(data, idx):
    print "  \\draw%s (0,0) " % decorations[idx % len(decorations)],
    last_y = 0
    for (x,y) in data:
        if x < 0.1:
            x = 0.1
        if x < max_time:
            lp = "(%f,%f)" % (time_to_x(x), perc_to_y(y))
            last_y = y
            print " -- %s" % lp,
    print " -- (%f, %f);" % (fig_width, perc_to_y(last_y))

def print_preamble(x_label = True):
    print "\\begin{tikzpicture}"
    # Draw axes
    print "  \\draw[->] (0,0) -- (0,5);"
    print "  \\draw[->] (0,0) -- (%f,0);" % fig_width
    # x ticks
    for i in abscissae:
        x = time_to_x(i)
        print "  \\node at (%f,0) [below] {%s};" % (x, i)
        print "  \\draw [color=black!10] (%f,0) -- (%f,%f);" % (x, x, perc_to_y(1))
    if x_label:
        print "  \\node at (%f,-12pt) [below] {Time to reproduce, seconds};" % (fig_width/2)
    # y ticks
    for i in xrange(0,11,2):
        y = perc_to_y(i/10.0)
        print "  \\node at (0,%f) [left] {%s\\%%};" % (y, render_nr(i* 10.0))
        print "  \\draw [color=black!10] (0,%f) -- (%f,%f);" % (y, fig_width, y)

