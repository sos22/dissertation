#! /bin/bash

grep "Crashing CFG has" DynRip* | sed  "s/Crashing CFG has \([0-9]*\) instructions/\1/p;d" > ~/work/thesis3/eval/phase_breakdown/instrs_per_probe
grep "Initial crashing machine" DynRip* | sed "s/Initial crashing machine has \([0-9]*\) states/\1/p;d" > ~/work/thesis3/eval/phase_breakdown/states_per_probe1
grep "Simplified crashing machine" DynRip* | sed "s/Simplified crashing machine has \([0-9]*\) states/\1/p;d" > ~/work/thesis3/eval/phase_breakdown/states_per_probe2
grep "getStoreCFGs" DynRip* | sed "s/getStoreCFGs took [0-9.]* seconds, produced \([0-9]*\)/\1/p;d" > ~/work/thesis3/eval/phase_breakdown/interfering_per_crashing
grep "Interfering CFG " DynRip* | sed "s,[0-9]*/[0-9]* Interfering CFG has \([0-9]*\) instructions,\1,p;d" > ~/work/thesis3/eval/phase_breakdown/instrs_per_interfering
grep "Initial interfering " DynRip* | sed "s,[0-9]*/[0-9]* Initial interfering StateMachine has \([0-9]*\) states,\1,p;d" > ~/work/thesis3/eval/phase_breakdown/states_per_interfering1
grep "Simplified interfering " DynRip* | sed "s,[0-9]*/[0-9]* Simplified interfering StateMachine has \([0-9]*\) states,\1,p;d" > ~/work/thesis3/eval/phase_breakdown/states_per_interfering2


