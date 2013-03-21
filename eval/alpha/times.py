import common

height1 = 7.0
height2 = 3.0
gap = 0.0

common.height = height1 + gap + height2 + 1

max_time = 0
include_timeouts = True

def time_to_y(time):
    return (time / max_time) * height1
    # if time >= max_time:
    #    return height1
    # if time < 0.1:
    #     return 0
    # else:
    #     return math.log(time / 0.1) / math.log(60/0.1) * height1

def timeout_to_y(frac):
    return height1 + height2 * frac + gap + 1

def draw_timeout_axis():
    print "  \\draw[->] (0,%f) -- (0,%f);" % (timeout_to_y(0), timeout_to_y(1))
    for p in xrange(0,101,20):
        y = timeout_to_y(p/100.0)
        print "  \\node at (0,%f) [left] {%d\\%%};" % (y, p)
        print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (y, common.width, y)
    print "  \\node at (0,%f) [rotate=90, left = 1,anchor=south] {Timeout rate};" % ((timeout_to_y(0) + timeout_to_y(1)) / 2)
    print "  \\draw[color=black!50] (0,%f) -- (%f,%f);" % (timeout_to_y(0), common.width, timeout_to_y(0))
def draw_time_axes(nr_ticks):
    print "  \\draw[->] (0,%f) -- (0,%f);" % (time_to_y(0), time_to_y(max_time))
    for t in xrange(0,nr_ticks+1):
        tt = int(t * max_time / nr_ticks)
        y = time_to_y(tt)
        print "  \\node at (0,%f) [left] {%d};" % (y, tt)
        print "  \\draw[color=black!10] (0,%f) -- (%f,%f);" % (y, common.width, y)
    print "  \\node at (0,%f) [rotate=90, left = 1,anchor=south] {Time taken, seconds};" % ((time_to_y(0) + time_to_y(max_time))/2)
    draw_timeout_axis()

def plot_timeout_chart(series):
    print "  \\draw (%f,%f)" % (common.alpha_to_x(0), timeout_to_y(0))
    for alpha in common.alphas:
        s = series[alpha]
        timeout_rate = float(s[0]) / (s[0] + len(s[1]))
        print "        -- (%f, %f)" % (common.alpha_to_x(alpha), timeout_to_y(timeout_rate))
    print "        ;"

def mk_percento(perc):
    assert perc >= 0
    assert perc < 1
    def doit(data):
        series = data[1]
        nr_timeouts = data[0]
        if include_timeouts:
            idx = (len(series) + nr_timeouts) * perc
        else:
            idx = len(series) * perc
        idx_low = int(idx)
        idx_high = idx_low + 1
        if idx_low >= len(series):
            return 60
        if idx_high == len(series):
            return series[-1]
        low = series[idx_low]
        high = series[idx_high]
        return low + (idx - idx_low) * (high - low)
    return doit
def mean(series):
    return sum(series[1])/float(len(series[1]))

def plot_times(series, show_legend, mapper):
    i = 0
    for (summariser, description) in lines:
        x = common.alpha_to_x(0)
        y = mapper(0)
        print "  \\draw%s (%f, %f)" % (common.decoration(i), x, y)
        last_x = x
        last_y = y
        for alpha in common.alphas:
            samples = series[alpha]
            y = mapper(summariser(samples))
            x = common.alpha_to_x(alpha)
            if last_y > height1:
                print "        -- (%f, %f)" % (common.width, height1)
            elif y > height1:
                print "        -- (intersection cs: first line={(%f,%f)--(%f,%f)}, second line={(0,%f)--(%f,%f)})" % (last_x, last_y, x, y, height1, common.width, height1)
                break
            else:
                print "        -- (%f, %f)" % (x, y)
            last_x = x
            last_y = y
        if show_legend:
            print "        node [color=black, right] {%s};" % description
        else:
            print "        ;"
        i += 1
    

lines = [(mk_percento(0.25), "25\\%"),
         (mk_percento(0.50), "50\\%"),
         (mk_percento(0.75), "75\\%"),
         (mean, "Mean")]
