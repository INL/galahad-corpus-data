#!/bin/bash
# Find all rows that match the given regexes. Order the output by source file.
# usage: 
#   regex-search.sh -l [lemma regex] -p [pos regex] -g [group_id regex] -t [token regex]
# example: 
#   find all proper nouns that start with a lowercase letter (suspicious!)
#      regex-search.sh -l "[a-z]+" -p "NOU\-P.*"

# parse args
while getopts "l:p:g:t:" opt; do
    case $opt in
        l) LEMMA_REGEX="$OPTARG" ;;
        p) POS_REGEX="$OPTARG" ;;
        g) GROUP_ID_REGEX="$OPTARG" ;;
        t) TOKEN_REGEX="$OPTARG" ;;
        *) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    esac
done
shift $((OPTIND - 1))

# check if at least one regex is given
if [ -z "$LEMMA_REGEX" ] && [ -z "$POS_REGEX" ] && [ -z "$GROUP_ID_REGEX" ] && [ -z "$TOKEN_REGEX" ]; then
    echo "Usage: $0 -l [lemma regex] -p [pos regex] -g [group_id regex] -t [token regex]"
    exit 1
fi

# to ease data analysis, concat all .tsv files in training-data into one file with an extra column "source_file"
files=$(find training-data -name "*.tsv")
for file in $files; do
    filename=$(basename "$file" | cut -d'.' -f1)
    awk -v source_file="$filename" 'BEGIN {FS=OFS="\t"} {print $0, source_file}' "$file"
done > tmp.tsv

# the tsv column order is: token pos lemma group_id source_file
awk -v lemma_regex="$LEMMA_REGEX" \
    -v pos_regex="$POS_REGEX" \
    -v group_id_regex="$GROUP_ID_REGEX" \
    -v token_regex="$TOKEN_REGEX" \
    'BEGIN {FS=OFS="\t"}
    {
        match_token = (token_regex == "" || $1 ~ token_regex)
        match_pos = (pos_regex == "" || $2 ~ pos_regex)
        match_lemma = (lemma_regex == "" || $3 ~ lemma_regex)
        match_group = (group_id_regex == "" || $4 ~ group_id_regex)
        if (match_lemma && match_pos && match_group && match_token) print
    }' tmp.tsv | sort -k4

rm tmp.tsv
