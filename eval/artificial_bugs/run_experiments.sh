#! /bin/bash

export SOS22_RUN_FOREVER=1

prefix=/local/scratch/sos22/sli/md_test_dir
harness=${prefix}/harness
#cat buglist | while read nr name; do ${harness} -n 100 '<none>' ${prefix}/bug${nr}.exe > ${name}.crash_times_data ; done
#cat buglist | while read nr name; do ${harness} -r -n 100 ${prefix}/bug${nr}~0.interp.so ${prefix}/bug${nr}.exe > ${name}~0.crash_times_data ; done
#cat buglist | while read nr name; do ${harness} -n 100 '<dc>' ${prefix}/bug${nr}.exe > ${name}~0.dc.crash_times_data ; done

#SOS22_DELAY_TX=1 ${harness} -l special/crash_indexed_toctou.delay_send.crash_times_data -r -n 100 ${prefix}/bug3~0.interp.so ${prefix}/bug3.exe
#SOS22_DELAY_RX=1 ${harness} -l special/crash_indexed_toctou.delay_recv.crash_times_data -r -n 100 ${prefix}/bug3~0.interp.so ${prefix}/bug3.exe
#SOS22_DELAY_ALWAYS=1 ${harness} -l special/crash_indexed_toctou.delay_both.crash_times_data -r -n 100 ${prefix}/bug3~0.interp.so ${prefix}/bug3.exe
#SOS22_DELAY_TX=1 ${harness} -l special/interfering_indexed_toctou.delay_send.crash_times_data -r -n 100 ${prefix}/bug4~0.interp.so ${prefix}/bug4.exe
#SOS22_DELAY_RX=1 ${harness} -l special/interfering_indexed_toctou.delay_recv.crash_times_data -r -n 100 ${prefix}/bug4~0.interp.so ${prefix}/bug4.exe
#SOS22_DELAY_ALWAYS=1 ${harness} -l special/interfering_indexed_toctou.delay_both.crash_times_data -r -n 100 ${prefix}/bug4~0.interp.so ${prefix}/bug4.exe

#${harness} -n 100 -l special/multi_var_fix_one_bug.crash_times_data ${prefix}/bug5~0.fix.so ${prefix}/bug5.exe
#SOS22_DISABLE_CTXT_CHECK=1 ${harness} -n 71 -l special/context_no_context.crash_times_data ${prefix}/bug6~0.interp.so ${prefix}/bug6.exe

unset SOS22_RUN_FOREVER

if false
then
    sample() {
	local t=$(mktemp)
	local preload=$1
	local exe=$2
	LD_PRELOAD=$preload $exe > $t
	grep "Survived" $t | sed 's/Survived, \([0-9]*\) read events and \([0-9]*\) write events.*/\1 \2/'
	rm -f "$t"
    }
    cat buglist | while read nr name
    do
	: > ${name}~0.perf_data
	for i in `seq 1 20`
	do
	    sample "${prefix}/bug${nr}~0.fix.so" "${prefix}/bug${nr}.exe" >>  ${name}~0.perf_data
	done
    done
fi

if false
then
    sample() {
	local t=$(mktemp)
	local exe=$1
	for i in `seq 1 100`
	do
	    $exe > $t && break
	done
	grep "Survived" $t | sed 's/Survived, \([0-9]*\) read events and \([0-9]*\) write events.*/\1 \2/'
	rm -f "$t"
    }
    cat buglist | while read nr name
    do
	: > ${name}.perf_data
	for i in `seq 1 20`
	do
	    sample "${prefix}/bug${nr}.exe" >>  ${name}.perf_data
	done
    done
fi