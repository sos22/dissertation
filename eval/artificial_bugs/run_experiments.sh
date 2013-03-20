#! /bin/sh

export SOS22_RUN_FOREVER=1
#cat buglist | while read nr name; do /local/scratch/sos22/sli/md_test_dir/harness -n 100 '<none>' /local/scratch/sos22/sli/md_test_dir/bug${nr}.exe > ${name}.crash_times_data ; done
cat buglist | while read nr name; do /local/scratch/sos22/sli/md_test_dir/harness -r -n 100 /local/scratch/sos22/sli/md_test_dir/bug${nr}~0.interp.so /local/scratch/sos22/sli/md_test_dir/bug${nr}.exe > ${name}~0.crash_times_data ; done
#cat buglist | while read nr name; do /local/scratch/sos22/sli/md_test_dir/harness -n 100 '<dc>' /local/scratch/sos22/sli/md_test_dir/bug${nr}.exe > ${name}~0.dc.crash_times_data ; done
