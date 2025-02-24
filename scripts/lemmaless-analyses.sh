# find all analyses where pos != PC, yet lemma is empty (which is incorrect, it should be filled)

# example regex: ^.*\t[^p][^c].*\t\t

files=$(find training-data -name "*.tsv")

matching_lines=""
pattern="^.*\t[^P][^C].*\t\t"

for file in $files
do
    matching_lines+=$(sed -n -r "/$pattern/p" $file)
    matching_lines+=$'\n'
done

echo "The following lines have been found:"
echo "$matching_lines" | sort | uniq
