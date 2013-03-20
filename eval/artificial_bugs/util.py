import math

fig_width = 6.0

decorations = ["", "[dashed]", "[dotted]"]
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
    return math.log(t/0.1) * fig_width / math.log(1800.0)

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

def print_preamble():
    print "\\begin{tikzpicture}"
    # Draw axes
    print "  \\draw[->] (0,0) -- (0,5);"
    print "  \\draw[->] (0,0) -- (%f,0);" % time_to_x(180)
    # x ticks
    for i in [0.1,0.5,1,2,4,8,16,32,64,180]:
        print "  \\node at (%f,0) [below] {%s};" % (time_to_x(i), i)
    # y ticks
    for i in xrange(0,11,2):
        print "  \\node at (0,%f) [left] {%s\\%%};" % (perc_to_y(i/10.0), render_nr(i* 10.0))


