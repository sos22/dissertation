import sys
import decimal

def float_range(lower, upper, step):
    lower = float(lower)
    while lower < upper:
        yield lower
        lower += step

class pushback:
    def __init__(self, underlying):
        self.q = []
        self.f = iter(underlying)
    def __iter__(self):
        return self
    def next(self):
        if len(self.q) == 0:
            return next(self.f)
        r = self.q[0]
        self.q = self.q[1:]
        return r
    def pushback(self, l):
        self.q.push(l)

def fail(msg):
    sys.stderr.write(msg);
    sys.stderr.write("\n");
    sys.exit(1)

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

def uniform_kernel(bandwidth, location):
    lower = location - bandwidth / 2.0
    upper = location + bandwidth / 2.0
    d = 1.0 / bandwidth
    def res(x):
        if lower <= x < upper:
            return d
        else:
            return 0
    return res
def truncated_uniform(upper_bound):
    def k(bandwidth, location):
        def res(x):
            if location + bandwidth / 2 < upper_bound:
                lower = location - bandwidth / 2
                upper = location + bandwidth / 2
            else:
                width = 2 * (upper_bound - location)
                if location > upper_bound:
                    sys.stderr.write("upper bound %f, location %f?\n" % (upper_bound, location))
                width *= bandwidth
                width **= .5
                lower = upper_bound - width
                upper = upper_bound
            assert upper <= upper_bound
            if lower <= x < upper:
                return 1.0 / (upper - lower)
            else:
                return 0
        return res
    return k
def guess_bandwidth(pts):
    # AMISE-optimal for a uniform kernel and a Gaussian distribution.

    # mean = sum(pts) / len(pts)
    # sd = (sum([ (x - mean)**2 for x in pts]) / len(pts))**.5

    # Calculate sd from inter-quartile range, rather than directly
    # from the data.  Produces the same results for gaussian data, but
    # less prone to outliers on non-gaussian.
    pts.sort()
    iqr = quantile(pts, 0.75) - quantile(pts, 0.25)
    sd = iqr / 1.34

    return 3.69 * sd / (len(pts) ** .2) / 2

def density_estimator(pts, kernel, bandwidth):
    if kernel == uniform_kernel:
        # The result is the number of pts between k - bandwidth / 2
        # and k + bandwidth /2, divided by the bandwidth.  That can be
        # calculated much more efficiently than the brute-force scheme
        # of just considering every point in turn.
        p = sorted(pts)
        def res(k):
            # Find the lower bound first.
            l = k - bandwidth / 2
            lower_lower = 0
            lower_upper = len(pts)
            while True:
                if lower_lower == lower_upper - 1 or lower_lower == lower_upper:
                    break
                guess_idx = (lower_lower + lower_upper) / 2
                guess = pts[guess_idx]
                if guess < l:
                    lower_lower = guess_idx
                else:
                    lower_upper = guess_idx
            # Linear scan for the last little bit
            lower = max(0, lower_lower - 2)
            while lower < lower_upper and pts[lower] < l:
                lower += 1

            # And now repeat that for the upper bound.
            u = k + bandwidth / 2
            upper_lower = lower - 1
            upper_upper = len(pts)
            while True:
                if upper_lower == upper_upper - 1 or upper_lower == upper_upper:
                    break
                guess_idx = (upper_lower + upper_upper) / 2
                guess = pts[guess_idx]
                if guess < u:
                    upper_lower = guess_idx
                else:
                    upper_upper = guess_idx
            upper = max(lower, upper_lower - 2)
            while upper < upper_upper and pts[upper] < u:
                upper += 1

            r =  (upper - lower) / bandwidth
            return r / len(pts)
        return res
    kernels = [kernel(bandwidth, d) for d in pts]
    def res(k):
        return sum([kernel(k) for kernel in kernels]) / len(kernels)
    return res

stdin = pushback(sys.stdin.xreadlines())
def get_line():
    l = next(stdin)
    w = l.split()
    assert w[0][-1] == ":"
    k = " ".join(w[1:])
    if k == "exit, status 0":
        return get_line()
    return (float(w[0][:-1]), k)

def draw_line(output, base, pts):
    first = True
    output.write("  \\draw ")
    last_zero = False
    for (y, deltax) in pts:
        if not first:
            output.write("        ")
            if deltax == 0 and last_zero:
                output.write("   ")
            else:
                output.write("-- ")
        first = False
        if deltax == 0:
            last_zero = True
        else:
            last_zero = False
        output.write("(%f, %f)\n" % (base + deltax, y))
    output.write("        ;\n")

def draw_furniture(output, chart_keys, settings):
    for t_label in ["0.00001", "0.0001", "0.001", "0.01", "0.1", "1", "10", "100", "300"]:
        y = settings.time_to_y(float(t_label))
        output.write("\\draw [color=black!10] (%f, %f) -- (%f, %f);\n" % (-settings.x_scale, y, (len(chart_keys) + 1) * settings.figwidth / (len(chart_keys) + 2), y))
        output.write("\\node at (%f, %f) [left] {%s};\n" % (-settings.x_scale, y, t_label))
    for box in settings.boxes:
        output.write("\\node at (%f, %f) [left] {%s};\n" % (-settings.x_scale, (box.lower + box.upper) / 2.0, box.label))
    output.write("\\node at (%f, %f) [left] {Kernel};\n" % (-settings.x_scale, settings.y_min - settings.kernel_box_height / 2))

class Chart(object):
    __slots__ = ["pre_dismissed", "pre_failed", "samples", "timeouts", "ooms"]
    def __init__(self):
        self.pre_dismissed = 0
        self.pre_failed = 0
        self.samples = []
        self.timeouts = 0
        self.ooms = 0
class Box(object):
    __slots__ = ["lower", "upper", "select1", "select2", "label"]
    def __init__(self, lower, upper, select1, select2, label):
        self.lower = lower
        self.upper = upper
        self.select1 = select1
        self.select2 = select2
        self.label = label
class Figure(object):
    __slots__ = ["figwidth", "maxtime", "mintime", "nr_time_steps",
                 "y_min", "y_max", "x_scale", "boxes", "time_to_y",
                 "y_to_time", "kernel_box_height"]
    def __init__(self, time_to_y, y_to_time, boxes):
        self.figwidth = 13.5
        self.maxtime = 500.0
        self.mintime = 0.000005
        self.nr_time_steps = 500.0
        self.y_min = 0.0
        self.y_max = 10.0
        self.x_scale = 0.5
        self.boxes = boxes
        self.kernel_box_height = 1.0

        self.time_to_y = time_to_y
        self.y_to_time = y_to_time
    def lowest(self):
        return min([self.y_min - self.kernel_box_height] + [box.lower for box in self.boxes])
    def highest(self):
        return max([self.y_max] + [box.upper for box in self.boxes])

def gini_coefficient(samples):
    n = len(samples)
    return 1 - (n - sum([(i * y) for (i,y) in enumerate(samples)]) / sum(samples)) * 2 / (n - 1)

def display_number(number, sd):
    n = decimal.Decimal(str(number))
    digits = pow(10, (decimal.Decimal(str(sd)).log10() - decimal.Decimal("0.5")).to_integral())
    n = (n / digits).quantize(decimal.Decimal("1")) * digits
    print "display_number(%s, %s) = %s" % (repr(number), repr(sd), repr(n))
    return n

# Samples should be in time space.
def plot_pdf(output, x, time_samples, replicated_samples, pdf_prob, settings, key):
    time_to_y = settings.time_to_y
    y_to_time = settings.y_to_time
    y_min = settings.y_min
    y_max = settings.y_max
    nr_time_steps = settings.nr_time_steps
    _quantile = quantile

    pdf_prob *= settings.x_scale

    # Convert samples from t-space to y-space.
    samples = map(time_to_y, time_samples)

    bw = guess_bandwidth(samples)

    pdf = density_estimator(samples, uniform_kernel, bw)
    densities = [(y, pdf(y) * pdf_prob) for y in float_range(y_min, y_max, (y_max - y_min) / nr_time_steps)]

    # White-out background region.
    output.write("  \\fill [color=white]")
    first = True
    last_zero = False
    for (y, deltax) in [(y, -d) for (y, d) in densities]:
        if not first:
            output.write("        ")
            if deltax == 0 and last_zero:
                output.write("-- ")
            else:
                output.write("-- ")
        first = False
        if deltax == 0:
            last_zero = True
        else:
            last_zero = False
        output.write("(%f, %f)\n" % (x + deltax, y))
    for (y, deltax) in reversed(densities[:-1]):
        if not first:
            output.write("        ")
            if deltax == 0 and last_zero:
                output.write("-- ")
            else:
                output.write("-- ")
        first = False
        if deltax == 0:
            last_zero = True
        else:
            last_zero = False
        output.write("(%f, %f)\n" % (x + deltax, y))
    output.write("        ;\n")

    # Plot the error region first
    replicates = [density_estimator(map(time_to_y, t), uniform_kernel, bw) for t in replicated_samples]

    # Figure out what we're doing
    inner_left = []
    outer_left = []
    inner_right = []
    outer_right = []
    for y in float_range(y_min, y_max, (y_max - y_min) / nr_time_steps):
        reps = sorted((r(y) for r in replicates))
        p05 = pdf_prob * _quantile(reps, 0.05)
        p95 = pdf_prob * _quantile(reps, 0.95)
        inner_left.append((x - p05, y))
        outer_left.append((x - p95, y))
        inner_right.append((x + p05, y))
        outer_right.append((x + p95, y))

    # Now do the left margin
    first = True
    output.write("  \\fill [color=black!50] ")
    for (x, y) in inner_left:
        if not first:
            output.write("        -- ")
        first = False
        output.write("(%f, %f)" % (x, y))
    for (x, y) in reversed(outer_left):
        output.write("        -- (%f, %f)" % (x, y))
    output.write("        ;\n")
    first = True
    # And the right one.
    output.write("  \\fill [color=black!50] ")
    for (x, y) in inner_right:
        if not first:
            output.write("        -- ")
        first = False
        output.write("(%f, %f)" % (x, y))
    for (x, y) in reversed(outer_right):
        output.write("        -- (%f, %f)" % (x, y))
    output.write("        ;\n")

    # Median line
    median = _quantile(samples, .5)
    medians = sorted((_quantile(map(time_to_y, r), .5) for r in replicated_samples))
    lower_median = _quantile(medians, 0.05)
    upper_median = _quantile(medians, 0.95)

    median_width = pdf(median) * pdf_prob
    lower_median_width = pdf(lower_median) * pdf_prob
    upper_median_width = pdf(upper_median) * pdf_prob
    output.write("  %% Medians: %s\n" % str(medians))
    output.write("  %% Median: %s\n" % str(y_to_time(median)))
    output.write("  \\fill [color=black!50] (%f, %f) -- (%f, %f) -- (%f, %f) -- (%f, %f) -- (%f, %f) -- (%f, %f) -- cycle;\n" % (x - lower_median_width, lower_median,
                                                                                                                                 x - median_width, median,
                                                                                                                                 x - upper_median_width, upper_median,
                                                                                                                                 x + upper_median_width, upper_median,
                                                                                                                                 x + median_width, median,
                                                                                                                                 x + lower_median_width, lower_median))
    output.write("  \\draw (%f, %f) -- (%f, %f); " % (x - median_width, median, x + median_width, median))

    # Now do the main PDF.
    draw_line(output, x, [(y, -d) for (y, d) in densities])
    draw_line(output, x, list(reversed(densities[:-1])))

    # Kernel
    bw_y = y_min - settings.kernel_box_height / 2
    output.write("  \\draw [fill=white] (%f, %f) rectangle (%f, %f);\n" % (x, bw_y - bw / 2, x + 1.0/bw * pdf_prob / len(samples), bw_y + bw / 2))

    # Mean + sd of mean
    mean = sum(time_samples) / len(time_samples)
    means = [sum(r) / len(r) for r in replicated_samples]
    means.sort()
    low_mean = quantile(means, 0.05)
    high_mean = quantile(means, 0.95)
    output.write("  %% mean = $%f \\in [%f, %f]_{%d}^{%d}$\n" % (mean, low_mean, high_mean,
                                                                 len(replicated_samples),
                                                                 len(time_samples)))
    mean_y = time_to_y(mean)
    low_mean_y = time_to_y(low_mean)
    high_mean_y = time_to_y(high_mean)
    output.write("  \\draw (%f,%f) -- (%f,%f);\n" % (x - .05, mean_y - .05,
                                                     x + .05, mean_y + .05))
    output.write("  \\draw (%f,%f) -- (%f,%f);\n" % (x + .05, mean_y - .05,
                                                     x - .05, mean_y + .05))
    output.write("  \\draw (%f,%f) -- (%f,%f);\n" % (x, low_mean_y,
                                                     x, high_mean_y))
    output.write("  \\draw (%f,%f) -- (%f,%f);\n" % (x-.05, low_mean_y,
                                                     x+.05, low_mean_y))
    output.write("  \\draw (%f,%f) -- (%f,%f);\n" % (x-.05, high_mean_y,
                                                     x+.05, high_mean_y))

    # Numerical mean display
    w = pdf(mean_y) * pdf_prob - 0.05
    # Bit of a hack: move the build strategy label a bit to avoid
    # overlapping
    if key == "build strategy":
        output.write("  \\node at (%f, %f) [left] {%s};\n" % (x - w, mean_y, display_number(mean, high_mean - low_mean)))
    else:
        output.write("  \\node at (%f, %f) [right] {%s};\n" % (x + w, mean_y, display_number(mean, high_mean - low_mean)))

def draw_box(output, x, box, chart, replicates, r_project, nr_samples, x_scale):
    if box.select1(chart) + box.select2(chart) == 0:
        return
    def chart_to_width(chart):
        box_prob = (box.select1(chart) + box.select2(chart)) / nr_samples
        box_area = box_prob * 2 * x_scale
        box_width = box_area / (box.upper - box.lower)
        return box_width
    rr = sorted((chart_to_width(r_project(r)) for r in replicates))
    lower_width = quantile(rr, 0.05)
    upper_width = quantile(rr, 0.95)
    width = chart_to_width(chart)

    def div_line(chart):
        d = box.select1(chart) + box.select2(chart)
        if d == 0:
            return None
        else:
            return float(box.select1(chart)) / (box.select1(chart) + box.select2(chart))
    rdiv = sorted(filter(lambda x: x != None, (div_line(r_project(r)) for r in replicates)))
    lower_div = quantile(rdiv, 0.05) * (box.upper - box.lower) + box.lower
    upper_div = quantile(rdiv, 0.95) * (box.upper - box.lower) + box.lower
    div = div_line(chart) * (box.upper - box.lower) + box.lower

    # Shaded region first
    output.write("  \\fill [color=black!50] (%f, %f) rectangle (%f, %f);\n" % (x - lower_width / 2, box.lower,
                                                                               x - upper_width / 2, box.upper))
    output.write("  \\fill [color=black!50] (%f, %f) rectangle (%f, %f);\n" % (x + lower_width / 2, box.lower,
                                                                               x + upper_width / 2, box.upper))
    output.write("  \\fill [color=black!50] (%f, %f) rectangle (%f, %f);\n" % (x - width / 2, lower_div,
                                                                               x + width / 2, upper_div))
    # Now the main box
    output.write("  \\draw [fill=white] (%f, %f) rectangle (%f, %f);\n" % (x - width / 2, box.lower, x + width / 2, box.upper))
    # And the division line
    output.write("  \\draw (%f, %f) -- (%f, %f);\n" % (x - width / 2, div, x + width / 2, div))
    # Count
    output.write("  \\node at (%f, %f) {%.2f\\%%};\n" % (x, (box.upper + box.lower) / 2.0, (box.select1(chart) + box.select2(chart)) * 100.0/nr_samples))

def draw_pdfs(output, chart_keys, charts, defect_samples, total_samples, replicates, chart_labels, settings):
    lowest = settings.lowest()
    for (idx, key) in enumerate(chart_keys):
        output.write("  %% Chart for %s\n" % key)
        chart = charts[key]
        x = idx * settings.figwidth / (len(chart_keys)+2)
        output.write("  \\node at (%f, %f) [below] {\\parbox{%fcm}{\center %s}};\n" % (x, lowest,
                                                                                       settings.figwidth / (len(chart_keys)+2),
                                                                                       chart_labels[key]))

        if len(chart.samples) == 0:
            continue

        nr_samples = len(chart.samples) #float(chart.pre_dismissed + chart.pre_failed + len(chart.samples) + chart.timeouts + chart.ooms)
        output.write("  %% largest sample = %f\n" % max(chart.samples))

        plot_pdf(output, x, chart.samples, [r[0][key].samples for r in replicates], len(chart.samples) / nr_samples, settings, key)

        # The PDF itself had area pdf_prob.  We will have drawn it
        # with area 2 * pdf_prob * x_scale cm2, so the scale factor we
        # need to apply to the other boxes is 2 * x_scale.
        for box in settings.boxes:
            draw_box(output, x, box, chart, replicates, lambda r: r[0][key], nr_samples, settings.x_scale)

    # And now do the total and defect
    x = len(chart_keys) * settings.figwidth / (len(chart_keys) + 2)
    plot_pdf(output, x, defect_samples, [r[1] for r in replicates], 1, settings, "defect")
    output.write("\\node at (%f,%f) [below] {Defect};\n" % (x, lowest))
    x = (len(chart_keys) + 1) * settings.figwidth / (len(chart_keys) + 2)
    plot_pdf(output, x, total_samples, [r[2] for r in replicates], 1, settings, "total")
    output.write("\\node at (%f,%f) [below] {Total};\n" % (x, lowest))

