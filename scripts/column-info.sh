# usage:
# ./scripts/column-info.sh --column 3

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

# get all tags for that column from all files in the training-data folder
TAGS=""
for file in $(find training-data -name "*.tsv")
do
    TAGS="$TAGS
$(cut -f $COLUMN $file)"
done

# some tags are so called multi tags, e.g. "A|B" or "A+B"
# split them and add them to the list
TAGS=$(echo "$TAGS" | tr '|' '\n' | tr '+' '\n')

echo "Tags in column sorted by frequency:"
echo "$TAGS" | sort | uniq -c | sort -nr