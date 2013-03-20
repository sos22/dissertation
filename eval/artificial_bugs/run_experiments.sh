#! /bin/sh

export SOS22_RUN_FOREVER=1

prefix=/local/scratch/sos22/sli/md_test_dir
harness=${prefix}/harness
#cat buglist | while read nr name; do ${harness} -n 100 '<none>' ${prefix}/bug${nr}.exe > ${name}.crash_times_data ; done
#cat buglist | while read nr name; do ${harness} -r -n 100 ${prefix}/bug${nr}~0.interp.so ${prefix}/bug${nr}.exe > ${name}~0.crash_times_data ; done
#cat buglist | while read nr name; do ${harness} -n 100 '<dc>' ${prefix}/bug${nr}.exe > ${name}~0.dc.crash_times_data ; done

SOS22_DELAY_TX=1 ${harness} -l special/crash_indexed_toctou.delay_send.crash_times_data -r -n 100 ${prefix}/bug3~0.interp.so ${prefix}/bug3.exe
SOS22_DELAY_RX=1 ${harness} -l special/crash_indexed_toctou.delay_recv.crash_times_data -r -n 100 ${prefix}/bug3~0.interp.so ${prefix}/bug3.exe
SOS22_DELAY_TX=1 ${harness} -l special/interfering_indexed_toctou.delay_send.crash_times_data -r -n 100 ${prefix}/bug4~0.interp.so ${prefix}/bug4.exe
SOS22_DELAY_RX=1 ${harness} -l special/interfering_indexed_toctou.delay_recv.crash_times_data -r -n 100 ${prefix}/bug4~0.interp.so ${prefix}/bug4.exe

