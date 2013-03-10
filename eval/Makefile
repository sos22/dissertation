CDFS=delta-perf/default.cdf delta-perf/neither.cdf delta-perf/no_dynamic.cdf delta-perf/no_load.cdf delta-perf/no_phi.cdf delta-perf/no_static.cdf
CDFS+=delta-perf/default.30.cdf delta-perf/neither.30.cdf delta-perf/no_dynamic.30.cdf delta-perf/no_load.30.cdf delta-perf/no_phi.30.cdf delta-perf/no_static.30.cdf

all: mysql-opt.tex $(CDFS) crash_times/simple_toctou.cdf

%.cdf: %.res timing_to_cdf.sh cdf.py
	./timing_to_cdf.sh $< $@.t && mv $@.t $@

mysql-opt.tex: mysql-opt-induction-rule.cdf mysql-opt-no-induction-rule.cdf mysql-opt.gpl
	gnuplot 'mysql-opt.gpl'

mysql-opt-induction-rule.cdf: mysql-opt-induction-rule.timings cdf.py 
	grep -v "timed out" $<  | sed 's/.* took //' | ./cdf.py `grep "timed out" $< | wc -l` > $@.t && mv $@.t $@
mysql-opt-no-induction-rule.cdf: mysql-opt-no-induction-rule.timings cdf.py 
	grep -v "timed out" $<  | sed 's/.* took //' | ./cdf.py `grep "timed out" $< | wc -l` > $@.t && mv $@.t $@

indexed_toctou_vary_nr_ptrs_enforcer.tex: indexed_toctou_vary_nr_ptrs_enforcer/p25 indexed_toctou_vary_nr_ptrs_enforcer/p50 indexed_toctou_vary_nr_ptrs_enforcer/p75 indexed_toctou_vary_nr_ptrs_enforcer/pmean indexed_toctou_vary_nr_ptrs_enforcer.gpl
	gnuplot indexed_toctou_vary_nr_ptrs_enforcer.gpl
indexed_toctou_vary_nr_ptrs_no_enforcer.tex: indexed_toctou_vary_nr_ptrs_no_enforcer/p25 indexed_toctou_vary_nr_ptrs_no_enforcer/p50 indexed_toctou_vary_nr_ptrs_no_enforcer/p75 indexed_toctou_vary_nr_ptrs_no_enforcer/pmean indexed_toctou_vary_nr_ptrs_no_enforcer.gpl
	gnuplot indexed_toctou_vary_nr_ptrs_no_enforcer.gpl

clean:
	rm -f *.aux *.cdf mysql-opt.tex