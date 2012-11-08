all: mysql-opt.tex

mysql-opt.tex: mysql-opt-induction-rule.cdf mysql-opt-no-induction-rule.cdf mysql-opt.gpl
	gnuplot 'mysql-opt.gpl'

mysql-opt-induction-rule.cdf: mysql-opt-induction-rule.timings cdf.py 
	grep -v "timed out" $<  | sed 's/.* took //' | ./cdf.py `grep "timed out" $< | wc -l` > $@.t && mv $@.t $@
mysql-opt-no-induction-rule.cdf: mysql-opt-no-induction-rule.timings cdf.py 
	grep -v "timed out" $<  | sed 's/.* took //' | ./cdf.py `grep "timed out" $< | wc -l` > $@.t && mv $@.t $@

clean:
	rm -f *.aux *.cdf mysql-opt.tex