# simplify-group-id.sh
# reduce the 4th column of all tsv files to IOB labels

# TSV files have the following columns:
# 1. token
# 2. lemma
# 3. part of speech
# 4. multi-word group

files=$(find training-data -name "*.tsv")
# in-place edit
for file in $files; do
    awk 'BEGIN {FS=OFS="\t"} {
        if (NF == 0) {
            print ""
        } else {
            if ($4 == "") {
                print $1, $2, $3, "O"
            } else if (NR == 1 || prev == "") {
                print $1, $2, $3, "B"
            } else {
                print $1, $2, $3, "I"
            }
        }
        prev = $4
    }' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
done