# print various information about the tsv training data

# print all unique tags in columns 2

TAGS=""
for file in $(find training-data -name "*.tsv")
do
    TAGS="$TAGS
$(cut -f3 $file | sort | uniq)"
done

# some tags are so called multi tags, e.g. "A|B" or "A+B"
# split them and add them to the list
TAGS=$(echo "$TAGS" | tr '|' '\n' | tr '+' '\n')

echo "Unique tags in column:"
echo "$TAGS" | sort | uniq