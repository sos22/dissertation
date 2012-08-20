#! /bin/sh

t=$(mktemp)
sed "s/$/\\\\\\\\ \\\\hline/;s/'//g" < sli.csv > "$t"
body=$(mktemp)
header=$(mktemp)
tail -n +2 "$t" > "$body"
head -n 1 "$t" > "$header"
rm -f "$t"

mk_header() {
    cat <<EOF
\begin{sidewaystable}
\centering
\begin{tabular}{p{1in}||p{0.3in}|p{0.9in}|p{.5in}|p{0.9in}|p{0.9in}|p{1in}|p{.8in}|p{1.1in}|p{.5in}|p{.5in}}
EOF
    cat $header
    echo "\\hline{}"
}
mk_footer() {
    cat <<EOF
\end{tabular}
\end{sidewaystable}
EOF
}

while [ -s "$body" ]
do
    this_time=$(mktemp)
    rest=$(mktemp)
    head -n 8 "$body" > $this_time
    tail -n +9 "$body" > $rest
    mk_header
    cat "$this_time"
    mk_footer
    mv "$rest" "$body"
    rm -f "$this_time"
done

rm -f "$header" "$body"
