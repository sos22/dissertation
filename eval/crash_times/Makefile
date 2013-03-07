enforcer_vs_no_enforcer=simple_toctou

enforcer_graphs=$(addsuffix .tex,$(enforcer_vs_no_enforcer))

all: $(enforcer_graphs)

%.tex: %__enforcer.cdf %__no_enforcer.cdf mk_tex.sh
	./mk_tex.sh $@

%.cdf: %.data mk_cdf.py
	./mk_cdf.py < $< > $@
