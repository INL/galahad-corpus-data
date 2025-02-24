#!/bin/bash

# suspicious.sh [--lemma | --pos] [--count MAX_COUNT] [--percent MAX_PERCENTAGE] [--per-file]
# Find suspicious analyses. Group all lines by token and lemma. Show a report of what part of speech is assigned to what percentage of the group (token,lemma).
#
# we consider a group to be suspicious if 
# - it has more than one part of speech assigned to it
# - one of those analyses occurs less than MAX_COUNT
# - the percentage of that analysis is less than MAX_PERCENTAGE

# default values
MAX_COUNT=5
MAX_PERCENTAGE=0.05
analyze_lemma=false
analyze_pos=false
per_file=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --lemma) analyze_lemma=true ;;
        --pos) analyze_pos=true ;;
        --per-file) per_file=true ;;
        --count) MAX_COUNT="$2"; shift ;;
        --percentage) MAX_PERCENTAGE="$2"; shift ;;
        *) echo "Unknown parameter passed: $1" >&2; exit 1 ;;
    esac
    shift
done

# exit if both analyses flags are set
if [[ $analyze_lemma == true && $analyze_pos == true ]]; then
    echo "Error: Cannot analyze by both lemma and part of speech" >&2
    exit 1
fi
# exit if neither analyses flag is set
if [[ $analyze_lemma == false && $analyze_pos == false ]]; then
    echo "Error: Must analyze by either lemma or part of speech" >&2
    exit 1
fi

# echo current settings
echo "MAX_COUNT: $MAX_COUNT"
echo "MAX_PERCENTAGE: $MAX_PERCENTAGE"
if [[ $analyze_lemma == true ]]; then
    echo "Analyzing by lemma"
else
    echo "Analyzing by part of speech"
fi
echo

# to ease data analysis, concat all .tsv files in training-data into one file with an extra column "source_file"
files=$(find training-data -name "*.tsv")
for file in $files; do
    filename=$(basename "$file" | cut -d'.' -f1)
    awk -v source_file="$filename" 'BEGIN {FS=OFS="\t"} {print $0, source_file}' "$file"
done > tmp.tsv

# TSV files have the following columns:
# 1. token
# 2. lemma
# 3. part of speech
# 4. multi-word group

# Use awk to process the concatenated TSV file
awk -F'\t' -v max_percentage=$MAX_PERCENTAGE -v max_count=$MAX_COUNT -v analyze_lemma=$analyze_lemma -v per_file=$per_file '
{
    # Create a unique key based on the analysis type
    # note the casing to ensure that the key is case-insensitive
    if (analyze_lemma == "true") {
        key = tolower($1) " " toupper($2)
    } else {
        key = tolower($1) " " toupper($3)
    }
    
    # Count the occurrences of each analysis and track source files
    if ($4 == "") { # if the fourth column is filled, it is not suspicious
        if (analyze_lemma == "true") {
            pos_count[key][$3]++
            pos_files[key][$3][$5]++
        } else {
            pos_count[key][$2]++
            pos_files[key][$2][$5]++
        }
    }
    
    # Count the total occurrences for this key
    total_count[key]++
}
END {
    # Loop through each unique key
    for (key in pos_count) {
        # Check if there is more than one POS for this key
        if (length(pos_count[key]) > 1) {
            suspicious = 0
            # Loop through each POS for this key
            for (pos in pos_count[key]) {
                # Check if the POS count is less than max_count and its percentage is less than max_percentage
                if ((pos_count[key][pos] / total_count[key]) <= max_percentage && pos_count[key][pos] <= max_count) {
                    if (pos != "") {
                        suspicious = 1
                        break
                    }
                }
            }
            # If the key is suspicious, prepare the result for this key
            if (suspicious) {
                result[key] = total_count[key] " " key
                split("", pos_sorted)
                # Sort POS counts in descending order
                n = asorti(pos_count[key], pos_sorted, "@val_num_desc")
                for (i = 1; i <= n; i++) {
                    pos = pos_sorted[i]
                    # only print suspicious analyses
                    if ((pos_count[key][pos] / total_count[key]) <= max_percentage && pos_count[key][pos] <= max_count) {
                        
                        # Append POS count and percentage to the result
                        result[key] = result[key] "\n\t\t" pos_count[key][pos] " (" sprintf("%.2f", (pos_count[key][pos] / total_count[key]) * 100) "%) " pos
                        
                        # Append source files to the result
                        result[key] = result[key] " "
                        for (file in pos_files[key][pos]) {
                            result[key] = result[key] file " "
                            # Track suspicious groups for each source file
                            suspicious_groups[file][key] = (key in suspicious_groups[file] ? suspicious_groups[file][key] "\n\t\t" : "") pos_count[key][pos] " (" sprintf("%.2f", (pos_count[key][pos] / total_count[key]) * 100) "%) " pos
                        }
                    }
                }
            }
        }
    }
    # Print suspicious groups for each source file, sorted by total occurrence of the key
    # Collect all keys and their total counts
    for (key in total_count) {
        all_keys[key] = total_count[key]
    }
    
    
    
    # Print suspicious groups for each source file, sorted by total occurrence of the key
    if (per_file == "true") {    
        # Sort all keys by total count in descending order
        n = asorti(all_keys, sorted_keys, "@val_num_desc")

        for (file in suspicious_groups) {
            print "===================================="
            print "Source: " file
            
            for (i = 1; i <= n; i++) {
                key = sorted_keys[i]
            
                if (key in suspicious_groups[file]) {
                    print total_count[key] " " key
                    print "\t\t" suspicious_groups[file][key]
                    print ""
                }
            }
        }
    } else {
        # Print the result for each key
        n = asorti(result, sorted_keys, "@val_num_desc")
        for (i = 1; i <= n; i++) {
            print result[sorted_keys[i]] "\n"
        }
    }
    
}
' tmp.tsv

# example output:
# 14430 van VAN
#         5 (0.03%) ADV(type=reg) dictionary-quotations-15 dictionary-quotations-16 dictionary-quotations-18 

# remove tmp file
rm tmp.tsv