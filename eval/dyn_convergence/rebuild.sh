for x in binlog_stm_drop_tbl innodb_multi_update rpl_change_master timestamp_basic 
do
	./plot.py $x.data narrow > $x.tex
done
./plot.py thunderbird.data scale > thunderbird.tex
./plot.py pbzip2.data > pbzip2.tex
