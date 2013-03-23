#! /bin/bash

t=$(mktemp)
chmod +x $t
cat > $t <<EOF
#! /usr/bin/env python

import sys
import math
import locale

sqrt20 = math.sqrt(20)

mean1 = float(sys.argv[1])
sd1 = float(sys.argv[2]) / sqrt20
mean2 = float(sys.argv[3])
sd2 = float(sys.argv[4]) / sqrt20

def leading_digit(d):
    if d < 0:
        d = -d
    if d < 1:
        cntr = 0
        while d < 1:
            d *= 10
            cntr += 1
        return -cntr
    else:
        cntr = -1
        while d >= 1:
            d /= 10
            cntr += 1
        return cntr

def print_range(lower, mean, higher):
    d = leading_digit(higher - lower) - 1
    def fmt(nr):
        r1 = "%.*f" % (-d, round(nr, -d))
        r2 = []
        f = False
        if r1.find(".") == -1:
            f = True
            cntr = 0
        for i in xrange(len(r1) - 1, -1, -1):
            if not f:
                r2.append(r1[i])
                if r1[i] == ".":
                    f = True
                cntr = 0
                continue
            if cntr == 3:
                r2.append(",\\\\!")
                cntr = 0
            cntr += 1
            r2.append(r1[i])
        r2.reverse()
        return "".join(r2)
    print "\$[%s; %s; %s]\$" % (fmt(lower), fmt(mean), fmt(higher)),

lower1 = mean1 - sd1 * 2
higher1 = mean1 + sd1 * 2
lower2 = mean2 - sd2 * 2
higher2 = mean2 + sd2 * 2

print_range(lower1, mean1, higher1)
print " & ",
print_range(lower2, mean2, higher2)
print " & ",
print_range(lower1 / higher2, mean1 / mean2, higher1 / lower2)
print "\\\\\\\"
EOF

escape() {
    echo "$1" | sed 's/_/\\_/g'
}

disposition() {
    if [ "$1" = "simple_toctou" ] ||
	[ "$1" = "context" ] ||
	[ "$1" = "double_free" ] ||
	[ "$1" = "existing_sync_visible" ] ||
	[ "$1" = "crash_indexed_toctou" ] ||
	[ "$1" = "existing_sync_invisible" ]
    then
	echo "read"
    elif [ "$1" = "interfering_indexed_toctou" ] ||
	[ "$1" = "write_to_read" ]
    then
	echo "write"
    elif [ "$1" = "indexed_toctou" ] ||
	[ "$1" = "multi_threads" ] ||
	[ "$1" = "complex_hb_5" ] ||
	[ "$1" = "complex_hb_17" ] ||
	[ "$1" = "complex_hb_11" ] ||
	[ "$1" = "w_isolation" ] ||
	[ "$1" = "broken_publish" ]
    then
	echo "both"
    elif [ "$1" = "multi_variable" ] ||
	[ "$1" = "multi_bugs" ] ||
	[ "$1" = "cross_function" ] ||
	[ "$1" = "glibc" ]
    then
	echo "neither"
    else
	echo "woobly woobly woo $1" >&2
	exit 1
    fi
}

do_one_line() {
    eval `<$1.perf_data cut -d' ' -f $2 | summarise_numbers.py | sed 's/ /=/' | tail -n +2`
    baseline_mean=$mean
    baseline_sd=$sd
    eval `<$1~0.perf_data cut -d' ' -f $2 | summarise_numbers.py | sed 's/ /=/' | tail -n +2`
    fixed_mean=$mean
    fixed_sd=$sd
    "$t" $baseline_mean $baseline_sd $fixed_mean $fixed_sd
}

cat buglist | while read ign bugname
do
    disp=$(disposition $bugname)
    if [ "$disp" = "neither" ]
    then
	continue
    fi

    printf "  \\\\multicolumn{2}{l}{%-30s} " $(escape $bugname)
    if [ "$disp" = "both" ]
    then
	echo "\\\\"
	echo -n "  & \multicolumn{1}{l}{Crashing thread} & "
	do_one_line $bugname 1
	echo -n "  & \multicolumn{1}{l}{Interfering thread} & "
	do_one_line $bugname 2
    elif [ "$disp" = "read" ]
    then
	echo -n " & "
	do_one_line $bugname 1
    elif [ "$disp" = "write" ]
    then
	echo -n " & "
	do_one_line $bugname 2
    else
	echo "Bad disposition $disp" >&2
	exit 1
    fi
done

echo $t

