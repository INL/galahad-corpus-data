# usage:
# ./scripts/column-info.sh --column [number] --filter [regex] [--split-multi] [--per-file]

# default values
COLUMN=3
SPLIT_MULTI=false
FILTER="." # regex
PER_FILE=false

# get column number from args
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --column) COLUMN="$2"; shift ;;
        --split-multi) SPLIT_MULTI=true ;;
        --per-file) PER_FILE=true ;;
        --filter) FILTER="$2"; shift ;;
        *) echo "Unknown parameter passed: $1" >&2; exit 1 ;;
    esac
    shift
done

# function to process tags
process_tags() {
    local TAGS="$1"
    if [ $SPLIT_MULTI = true ]; then
        TAGS=$(echo "$TAGS" | tr '|' '\n' | tr '+' '\n')
    fi
    TAGS=$(echo "$TAGS" | grep -E "$FILTER")

    # don't echo when tags are empty
    if [ -z "$TAGS" ]; then
        echo "None found"
        return
    fi

    echo "$TAGS" | sort | uniq -c | sort -nr
}

if [ $PER_FILE = true ]; then
    for file in $(find training-data -name "*.tsv")
    do
        TAGS=$(cut -f $COLUMN $file)
        echo "$file:"
        process_tags "$TAGS"
        echo
    done
else
    TAGS=""
    for file in $(find training-data -name "*.tsv")
    do
        TAGS="$TAGS
$(cut -f $COLUMN $file)"
    done
    echo "Tags in column sorted by frequency:"
    process_tags "$TAGS"
fi
