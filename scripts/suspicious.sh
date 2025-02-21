#!/bin/bash

# suspicious.sh:
# Find suspicious analyses.
# step 1: find all lemmas with a comma in them
# step 2: group all lines by token and lemma. Show a report of what part of speech is assigned to what percentage of the group (token,lemma).

# Data is in the form of tsv files with the following columns:
# 1: token
# 2: part of speech
# 3: lemma

# step 1
# skip for now

# step 2
# to ease data analysis, concat all .tsv files in training-data into one file
files=$(find training-data -name "*.tsv")
cat $files > all.tsv

# group all lines by lemma and token. Show a report of what part of speech is assigned to what percentage of the group (lemma,token).

# we consider a group to be suspicious if it has more than one part of speech assigned to it
# and if one of those parts of speech assigment only occurs in less than 1% of the cases


awk -F'\t' '
{
    key = $3 "\t" $1
    pos_count[key][$2]++
    total_count[key]++
}
END {
    for (key in pos_count) {
        if (length(pos_count[key]) > 1) {
            suspicious = 0
            for (pos in pos_count[key]) {
                if ((pos_count[key][pos] / total_count[key]) < 0.01) {
                    suspicious = 1
                    break
                }
            }
            if (suspicious) {
                result[key] = total_count[key] "\t" key
                for (pos in pos_count[key]) {
                    result[key] = result[key] sprintf("\t%s: %.2f%%", pos, (pos_count[key][pos] / total_count[key]) * 100)
                }
            }
        }
    }
    n = asorti(result, sorted_keys, "@val_num_desc")
    for (i = 1; i <= n; i++) {
        print result[sorted_keys[i]]
    }
}
' all.tsv