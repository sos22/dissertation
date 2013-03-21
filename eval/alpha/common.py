import sys

width = 12

alphas = [10, 20, 30, 40, 50, 75, 100]

decorations = [ "", "[dotted]", "[dashed]", "[color=black!50]"]
def decoration(idx):
    return decorations[idx % len(decorations)]

def alpha_to_x(alpha):
    return alpha / 100.0 * width

def fail(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)

def draw_alpha_axis():
    print "  \\draw[->] (0,0) -- (%f,0);" % width
    for alpha in alphas:
        x = alpha_to_x(alpha)
        print "  \\node at (%f,0) [below] {%d};" % (x, alpha)
        print "  \\draw[color=black!10] (%f,0) -- (%f,%f);" % (x, x, height)
    print "  \\node at (%f,0) [below = 1] {Value of $\\alpha$};" % (alpha_to_x(alphas[-1]/2.0))
