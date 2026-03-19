1. Download TEI from Lancelot with `download.py`
2. Normalize the TEI with `tei-normalizer.py`
3. Convert TEI to TSV with `convert.py`
4. Fix TSV columns with `fix-tsv-columns.py`
5. Create splits with `split.py`

Example pipeline

```sh
scripts/export/download.py source-data
scripts/export/tei-normalizer.py -r source-data
jing tei_all.rng *
scripts/export/upload.py -f -r source-data
scripts/export/convert.py source-data tsv-data
scripts/export/fix-tsv-columns.py -r tsv-data
scripts/export/split.py tsv-data training-data
scripts/analyses/duplicate-checker.py
scripts/export/group_dupes_in_split.py
scripts/analyses/statistics.py training-data statistics
```

# Validation

Can be done with [jing](https://relaxng.org/jclark/jing.html) (`apt install jing`) or scripts/export/tei-validator.py
