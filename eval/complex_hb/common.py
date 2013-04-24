import os

fig_width = 14.0
fig_height = 8.0
error_bar_width = 0.1

def count_to_x(count):
    return count / 100.0 * fig_width

def load_data(re):
    data = {}
    for f in os.listdir("."):
        m = re.match(f)
        if m == None:
            continue
        idx = int(m.group(1))
        fl = file(f)
        samples = [float(l.strip()) for l in fl.xreadlines()]
        fl.close()
        mean = sum(samples) / float(len(samples))
        sd = (sum([(x - mean) ** 2 for x in samples]) / (len(samples) * (len(samples) - 1.0))) ** .5
        data[idx] = (mean, sd)
    return data

def preamble():
    print "\\begin{tikzpicture}"

def x_axis():
    print "  %% X axis"
    print "  \\draw[->] (0,0) -- (%f,0);" % fig_width
    for a in ["0", "10", "20", "30", "40", "50", "60", "70", "73", "80", "90", "100"]:
        x = count_to_x(float(a))
        print "  \\node at (%f, 0) [below] {%s};" % (x, a)
        print "  \\draw[color=black!10] (%f,0) -- (%f,%f);" % (x, x, fig_height)
    print "  \\node at (%f,-12pt) [below] {Number of edges};" % (fig_width/2)

def y_axis(labels, time_to_y):
    print "  %% Y axis"
    print "  \\draw[->] (0,0) -- (0,%f);" % fig_height
    for a in labels:
        y = time_to_y(float(a))
        print "  \\node at (0, %f) [left] {%s};" % (y, a)
        print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (y, fig_width, y)
    print "  \\node at (-12pt,%f) [rotate=90,left = 1, anchor = north] {Time to build \\glspl{verificationcondition}, seconds};" % (fig_height / 2)

def plot_data(time_to_y, data):
    # And the data
    data = data.items()
    data.sort()
    print "  %% Main data"
    for (count, (time, sd)) in data:
        w = error_bar_width / 2
        x = count_to_x(count)
        mean = time_to_y(time)
        lower = time_to_y(time - sd)
        upper = time_to_y(time + sd)
        print "  \\draw (%f,%f) -- (%f,%f);" % (x - w, mean - w, x + w, mean + w)
        print "  \\draw (%f,%f) -- (%f,%f);" % (x + w, mean - w, x - w, mean + w)
        print "  \\draw (%f,%f) -- (%f,%f);" % (x, lower, x, upper)
        print "  \\draw (%f,%f) -- (%f,%f);" % (x - w, lower,
                                                x + w, lower)
        print "  \\draw (%f,%f) -- (%f,%f);" % (x - w, upper,
                                                x + w, upper)

def postamble():
    print "\\end{tikzpicture}"
