# print all unique tags in a column
# usage:
# ./scripts/unique-tags-in-column.sh --column 3

# default values
COLUMN=3

# get column number from args
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --column) COLUMN="$2"; shift ;;
        *) echo "Unknown parameter passed: $1" >&2; exit 1 ;;
    esac
    shift
done


TAGS=""
for file in $(find training-data -name "*.tsv")
do
    TAGS="$TAGS
$(cut -f $COLUMN $file | sort | uniq)"
done

# some tags are so called multi tags, e.g. "A|B" or "A+B"
# split them and add them to the list
TAGS=$(echo "$TAGS" | tr '|' '\n' | tr '+' '\n')

echo "Unique tags in column:"
echo "$TAGS" | sort | uniq