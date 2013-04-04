import sys
import math

# Reduce data by just ignoring any move of less than a certain amount.
# Amount is calculated so that the picture looks the same when printed
# at some dpi
dpi = 1000

skip_reduction = False

def fail(s):
    sys.stderr.write("%s\n" % s)
    sys.exit(1)

lookahead = None
def get_line():
    global lookahead
    if lookahead:
        r = lookahead
        lookahead = None
        return r
    l = sys.stdin.readline().strip()
    if l == "":
        return None
    w = l.split(" ")
    if w[0][-1] != ":":
        fail("line %s has no timestamp" % l)
    ts = float(w[0][:-1])
    return (ts, w[1:])

def transpose_bubbles(series, dilation, bubble_keys):
    defect_bubble = []
    for s in series:
        defect = s[0]
        for k in bubble_keys:
            if s[1].has_key(k):
                defect -= s[1][k]["time"]
        defect_bubble.append(defect)
    defect_bubble.sort(reverse=True)

    dismiss = 0
    failed = 0
    offset = 0
    max_nr_samples = 0
    bubbles = {}
    for k in bubble_keys:
        rel = [s[1] for s in series if s[1].has_key(k)]
        b = {"dismiss": dismiss,
             "failed":  failed,
             "samples": [s[k]["time"] for s in rel] }
        dismiss += len([x for x in rel if x[k]["dismiss"]])
        failed += len([x for x in rel if x[k]["failed"]])
        if len(b["samples"]) > max_nr_samples:
            max_nr_samples = len(b["samples"])
        w = sum(b["samples"]) / len(b["samples"])
        b["offset"] = (offset + w) * dilation
        b["samples"].sort(reverse = True)
        bubbles[k] = b
        offset += w
        max_time = offset + w

    gc = []
    for s in series:
        if s[1].has_key("GC"):
            gc.append(s[1]["GC"]["time"])
        else:
            gc.append(0)
    gc.sort(reverse = True)
    w = sum(gc) / len(gc)
    bubbles["GC"] = {"dismiss": 0,
                     "failed": 0,
                     "samples": gc,
                     "offset": (offset + w) * dilation}
    w = sum(defect_bubble) / len(defect_bubble)
    bubbles["defect"] = {"dismiss": 0,
                         "failed": 0,
                         "samples": defect_bubble,
                         "offset": (offset + w) * dilation}
    offset += w + 1
    return (bubbles, max_time, max_nr_samples)

def print_preamble(x_labels, y_legend, scale_time, legend_nr_seconds, legend_step, figwidth, figheight):
    print "\\begin{tikzpicture}"
    print "  %% x axis"
    print "  \\draw[->] (0,0) -- (%f,0);" % figwidth
    for l in x_labels:
        print "  \\node at (%f,0) [below] {%s};" % (l["posn"], l["label"])
    print "  \\node at (%f,0) [below] {Other};" % (figwidth + 1)
    print "  \\node at (%f,-12pt) [below] {Average phase finish times, seconds};" % (figwidth / 2)

    print "  %% second x scale"
    legend_width = scale_time(legend_nr_seconds)
    legend_start = (figwidth - legend_width) / 2
    legend_end = (figwidth + legend_width) / 2
    print "  \\draw (%f, -36pt) -- (%f, -36pt);" % (legend_start, legend_end)
    for i in xrange(0, legend_nr_seconds + 1, legend_step):
        print "  \\node at (%f, -36pt) [below] {%d};" % (legend_start + scale_time(i), i)
    print "  \\node at (%f, -48pt) [below] {Duration of individual phases, seconds};" % (figwidth / 2)

    print "  %% y axis"
    print "  \\draw[->] (0,0) -- (0,%f);" % figheight
    for i in xrange(0, 101, 10):
        print "  \\node at (0,%f) [left] {%d\\%%};" % (figheight * i / 100.0, i)
    print "  \\node at (-30pt,%f) [rotate=90, left, anchor = south] {%s};" % (figheight / 2, y_legend)


def label_bubbles(labels, scale_time, scale_idx, bubbles, y_centrums, dilation, fh, fw):
    print "  %% bubble labels"
    for (key, data) in labels.iteritems():
        if key == "defect":
            x = fw + 1
        else:
            x = scale_time(bubbles[key]["offset"])
        print "  \\draw [color=blue!50] (%f,%f) node [color=black, %s] {\!\!%s\!\!} -- (%f,%f);" % (scale_time(data["posn"][0][0]*dilation),
                                                                                                    data["posn"][0][1] * fh,
                                                                                                    data["posn"][1],
                                                                                                    data["label"],
                                                                                                    x,
                                                                                                    scale_idx(y_centrums[key] * len(bubbles[key]["samples"])))

def displacement_vector(ptA, ptB):
    return (ptB[0] - ptA[0], ptB[1] - ptA[1])
def vector_magnitude(ptA):
    return math.sqrt(ptA[0] ** 2 + ptA[1] ** 2)
def vector_scale(v, s):
    return (v[0] * s, v[1] * s)
def dot_product(a, b):
    return a[0] * b[0] + a[1] * b[1]
def vector_add(a, b):
    return (a[0] + b[0], a[1] + b[1])
def distance(a, b):
    return vector_magnitude(displacement_vector(a, b))
def unit_vector(a):
    return vector_scale(a, 1/vector_magnitude(a))

def draw_bubbles(bubble_keys, bubbles, labels, y_centrums, scale_time, scale_idx, dilation, figheight, figwidth):
    bubble_keys = bubble_keys + ["defect"]
    reordered_samples = {}
    for key in bubble_keys:
        bubble = bubbles[key]
        samples = bubble["samples"]
        above_list = []
        below_list = []
        ratio = y_centrums[key]
        for idx in xrange(len(samples)):
            b_targ = idx * (1 - ratio)
            s = samples[idx]
            if idx * (1 - ratio) < len(below_list):
                above_list.append(s)
            else:
                below_list.append(s)
        above_list.reverse()
        reordered_samples[key] = above_list + below_list
    min_move = 2.55 / dpi
    points = {}
    for key in bubble_keys:
        pts = []
        samples = reordered_samples[key]
        bubble = bubbles[key]
        if key == "defect":
            x_base = figwidth + 1
        else:
            x_base = scale_time(bubble["offset"])
        def add_pt(new_pt):
            if skip_reduction or len(pts) == 0 or distance(new_pt, pts[-1]) >= min_move:
                pts.append(new_pt)
        for idx in xrange(len(samples)):
            add_pt((x_base - scale_time(samples[idx] / 2), scale_idx(idx)))
        for idx in xrange(len(samples) - 1, 0, -1):
            add_pt((x_base + scale_time(samples[idx] / 2), scale_idx(idx)))
        points[key] = pts
    def draw_blob(command):
        for key in bubble_keys:
            print "  %%%% Bubble for %s" % key
            pts = points[key]
            # Now go and plot them.
            last_pt = pts[0]
            print "  %s (%f, %f)" % (command, last_pt[0], last_pt[1])
            idx = 1
            while idx < len(pts) - 1:
                # Try to use the longest straight line we can get away with
                start_pt = last_pt
                first_pt = pts[idx]
                if first_pt == start_pt:
                    idx+=1
                    continue
                nr_pts_in_line = 1
                vect1 = displacement_vector(start_pt, first_pt)
                line_len = vector_magnitude(vect1)
                vect1 = unit_vector(vect1)
                while not skip_reduction and nr_pts_in_line + idx < len(pts):
                    # What error would be introduced by approximating this
                    # point with the line?
                    vect2 = displacement_vector(start_pt, pts[nr_pts_in_line+idx])
                    mag = vector_magnitude(vect2)
                    approximant = vector_scale(vect1, mag)
                    defect = vector_magnitude(displacement_vector(approximant, vect2))
                    if defect > min_move or mag < line_len:
                        break
                    line_len = mag
                    nr_pts_in_line += 1
                v = vector_add(start_pt, vector_scale(vect1, line_len))
                print "        -- (%f,%f) %% %d points" % (v[0], v[1], nr_pts_in_line)
                last_pt = pts[idx+nr_pts_in_line-1]
                idx += nr_pts_in_line
            # Close it off.
            print "        (%f, %f) -- (%f, %f);" % (pts[-1][0], pts[-1][1], pts[0][0], pts[0][1])
    draw_blob("\\draw[color=black!10]")
    label_bubbles(labels, scale_time, scale_idx, bubbles, y_centrums, dilation, figheight, figwidth)
    draw_blob("\\fill")

def draw_line_series(scale_idx, scale_time, max_nr_samples, bubble_keys, bubbles, figwidth, figheight):
    # Plot the dismissed line
    print "  \\draw (0,%f)" % scale_idx(max_nr_samples)
    for k in bubble_keys:
        bubble = bubbles[k]
        print "        -- (%f, %f)" % (scale_time(bubble["offset"]), scale_idx(max_nr_samples - bubble["dismiss"]))
    print "        ;"

    # And the timeout line
    print "  \\draw [dashed] (0,%f)" % scale_idx(max_nr_samples)
    for k in bubble_keys:
        bubble = bubbles[k]
        print "        -- (%f, %f)" % (scale_time(bubble["offset"]), scale_idx(max_nr_samples - bubble["dismiss"] - bubble["failed"]))
    print "        ;"

    # Legend for them
    print "  \\node at (%f,%f) [below left] {\\shortstack[l]{" % (figwidth, figheight)
    print "      \\raisebox{1mm}{\\tikz{\\draw (0,0) -- (1,0);}} Dismissed early \\\\"
    print "      \\raisebox{1mm}{\\tikz{\\draw[dashed] (0,0) -- (1,0);}} Timeouts"
    print "  }};"


def print_trailer(figwidth, figheight):
    print "\\end{tikzpicture}"
