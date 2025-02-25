
# This script is used to clean up the training data.

#################################
# Functions
#################################

# replace_lines(pattern, replacement)
# pattern:
#     Regex pattern to match lines that should be replaced.
# replacement:
#     Replacement string. If "DELETE", the line will be deleted.
function replace_lines {
    local pattern=$1
    local replacement=$2
    local files=$(find training-data -name "*.tsv")
    local matching_lines=""

    for file in $files
    do
        matching_lines+=$(sed -n -r "/$pattern/p" $file)
        matching_lines+=$'\n'
    done

    echo "The following lines have been processed:"
    echo "$matching_lines" | sort | uniq

    # then replace or delete them
    for file in $files
    do
        if [ "$replacement" == "DELETE" ]; then
            sed -i -r "/$pattern/d" $file
        else
            # note the use of /g here
            # or example: a line may contain multiple soft hyphens that need replacing
            sed -i -r "s/$pattern/$replacement/g" $file
        fi
    done
}

#################################
# Main
#################################

# use explicit variables for capture groups to improve readability
C1="\1"
C2="\2"
C3="\3"
C4="\4"
C5="\5"
ANY="(.*)"

# annotate all untagged punctuation with PC
PUNCTUATION="([][…\.,;!?¶&'„│—\":]+)"
echo "Annotating untagged punctuation with PC..."
replace_lines "^$PUNCTUATION\t\t\t$" "$C1\tPC\t\t"

# also, some files have doc ids that need to be removed
# e.g. pc-00531111
DOC_ID="pc-[0-9]+"
# simply remove the entire line
echo "Removing lines with document ids..."
replace_lines "^$DOC_ID\t\t\t$" "DELETE"

# some punctuation is tagged as no_pos, so replace it with PC
echo "Replacing no_pos with PC..."
replace_lines "^$PUNCTUATION\tno_pos\t\t$" "$C1\tPC\t\t"

# some punctuation is tagged as an underscore, so replace it with PC
echo "Replacing _ with PC..."
replace_lines "^$PUNCTUATION\t_\t\t$" "$C1\tPC\t\t"

# some punctuation is tagged as a post, so replace it with PC
echo "Replacing post with PC..."
replace_lines "^$PUNCTUATION\tpost\t\t$" "$C1\tPC\t\t"

# some punctuation is tagged as a pre, so replace it with PC
echo "Replacing pre with PC..."
replace_lines "^$PUNCTUATION\tpre\t\t$" "$C1\tPC\t\t"

# some multiple analysis lemmata have a \uE280AF character in them (narrow no-break space)
# remove it
echo "Removing narrow no-break space..."
replace_lines "\xE2\x80\xAF" ""

# replace \' with '
echo "Replacing \\' with '..."
replace_lines "\\\\'" "'"

# remove soft hyphen (\uC2AD)
echo "Removing soft hyphen..."
replace_lines "\xC2\xAD" ""

# replace non-breaking hyphen (\u2011) with normal hyphen
echo "Replacing non-breaking hyphen with normal hyphen..."
replace_lines "\xE2\x80\x91" "-"

# replace ’ with ' but only in lemmas
echo "Replacing ’ with ' in lemmas..."
replace_lines "^$ANY\t$ANY\t$ANY’$ANY\t$ANY$" "$C1\t$C2\t$C3'$C4\t$C5"

# some multi-pos (with OR |) have the same pos on both sides of the OR
# e.g. "ADV|ADV"
# remove the duplicate
echo "Removing duplicate pos in multi-OR-pos..."
replace_lines "^$ANY\t$ANY\|(\2)\t$ANY\t$ANY$" "$C1\t$C2\t$C4\t$C5"

# same for lemmas
echo "Removing duplicate lemmas in multi-OR-lemmas..."
replace_lines "^$ANY\t$ANY\t$ANY\|(\3)\t$ANY$" "$C1\t$C2\t$C3\t$C5"

# remaining unanalysed tokens can be deleted
echo "Removing unanalysed tokens..."
replace_lines "^$ANY\t\t\t$" "DELETE"