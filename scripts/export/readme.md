1. Download TEI from Lancelot with `download.py`
2. Normalize the TEI with `tei-normalizer.py`
3. Convert TEI to TSV with `convert.py`
4. Fix TSV columns with `fix-tsv-columns.py`
5. Create splits with `split.py`

Example pipeline

```sh
scripts/export/download.py lancelot
scripts/export/tei-normalizer.py -r lancelot
scripts/export/convert.py lancelot galahad
scripts/export/fix-tsv-columns.py -r galahad
scripts/export/split.py galahad training-data
scripts/analyses/statistics.py training-data statistics
```

# Validation

Can be done with [jing](https://relaxng.org/jclark/jing.html) (`apt install jing`) or scripts/export/tei-validator.py
