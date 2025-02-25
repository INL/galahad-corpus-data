# simplify-group-id.sh
# reduce the 4th column of all tsv files to simply true or false
# depending on whether a group id is present or not

# TSV files have the following columns:
# 1. token
# 2. lemma
# 3. part of speech
# 4. multi-word group

files=$(find training-data -name "*.tsv")
# in-place edit
for file in $files; do
    awk 'BEGIN {FS=OFS="\t"} {if (NF == 0) print ""; else print $1, $2, $3, ($4 == "") ? "" : "group"}' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
done