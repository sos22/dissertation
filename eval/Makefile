CDFS=delta-perf/default.cdf delta-perf/neither.cdf delta-perf/no_dynamic.cdf delta-perf/no_load.cdf delta-perf/no_phi.cdf delta-perf/no_static.cdf

all: mysql-opt.tex $(CDFS)

%.cdf: %.res timing_to_cdf.sh cdf.py
	./timing_to_cdf.sh $< $@.t && mv $@.t $@

mysql-opt.tex: mysql-opt-induction-rule.cdf mysql-opt-no-induction-rule.cdf mysql-opt.gpl
	gnuplot 'mysql-opt.gpl'

mysql-opt-induction-rule.cdf: mysql-opt-induction-rule.timings cdf.py 
	grep -v "timed out" $<  | sed 's/.* took //' | ./cdf.py `grep "timed out" $< | wc -l` > $@.t && mv $@.t $@
mysql-opt-no-induction-rule.cdf: mysql-opt-no-induction-rule.timings cdf.py 
	grep -v "timed out" $<  | sed 's/.* took //' | ./cdf.py `grep "timed out" $< | wc -l` > $@.t && mv $@.t $@


clean:
	rm -f *.aux *.cdf mysql-opt.tex