#! /bin/bash

get_mean_sd() {
    eval `<$1 summarise_numbers.py | sed 's/ /=/' | tail -n +2`
    printf "\$%.3f \\pm %.3f\$" $mean $sd
}

escape() {
    echo "$1" | sed 's/_/\\_/g'
}

cat buglist | while read ign bugname
do
    printf "  %-30s &" $(escape $bugname)
    for field in db.timing build_summary_time
    do
	s=$(get_mean_sd $bugname.$field)
	echo -n " $s & "
    done
    if [ "$bugname" != multi_bugs ]
    then
	for field in build_interp_time build_fix_time
	do
	    s=$(get_mean_sd $bugname~0.$field)
	    echo -n " $s & "
	done | sed 's/ & $//'
	echo "\\\\"
    else
	echo "\\\\"
	for idx in 0 1
	do
	    echo -n " \\hspace{5mm}Bug $(($idx + 1)) & & & "
	    for field in build_interp_time build_fix_time
	    do
		s=$(get_mean_sd $bugname~${idx}.$field)
		echo -n " $s & "
	    done | sed 's/ & $//'
	    echo "\\\\"
	done
    fi
done
