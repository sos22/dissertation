#! /bin/sh

set -e
set -x

./process_bubble_log.py < bubble1.log > bubble1.tex
./process_bubble_log2.py < bubble2.log > bubble2.tex
./process_bubble_log3.py < bubble3.log > bubble3.tex
./process_bubble_log4.py < bubble4.log > bubble4.tex


