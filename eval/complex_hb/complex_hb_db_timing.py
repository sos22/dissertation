#! /usr/bin/env python

import re
import common

def time_to_y(t):
    return (t - 1.5) / (2.3 - 1.5) * common.fig_height

data = common.load_data(re.compile(r"complex_hb_([0-9]*)\.db\.timing"))
common.preamble()
common.x_axis()
common.y_axis(["1.5", "1.7", "1.9", "2.1", "2.3"], time_to_y)
common.plot_data(time_to_y, data)
common.postamble()
