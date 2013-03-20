#! /bin/bash

set -e

get_mean_sd() {
    eval `<$2 cut -d' ' -f $1 | summarise_numbers.py | sed 's/ /=/' | tail -n +2`
    printf "\$%.3f \\pm %.3f\$" $mean $sd
}

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
    get_mean_sd $2 $1.perf_data
    echo -n " & "
    get_mean_sd $2 $1~0.perf_data
    echo -n " & "
    eval `cut -d' ' -f $2 ${1}.perf_data | summarise_numbers.py | sed 's/ /=/' | tail -n +2`
    base=${mean}
    eval `cut -d' ' -f $2 ${1}~0.perf_data | summarise_numbers.py | sed 's/ /=/' | tail -n +2`
    val=${mean}
    echo -n $(python -c "print \"%.2f\" % (${val}/${base}),")
    echo "\\\\"
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
