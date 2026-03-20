# Data processing pipeline

1. Download the TEI from Lancelot.

    `python3 -m scripts.web.download source-data/`

2. Normalize the TEI.

    `python3 -m scripts.normalizer -r source-data/`

3. Validate with [jing](https://relaxng.org/jclark/jing.html) (`apt install jing`) using [tei_all.rng](https://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng).

    `jing scripts/validator/tei_all.rng source-data/*/*`

4. Convert TEI to TSV with Galahad.

    `python3 -m scripts.web.convert -r source-data/ tsv-data/`

5. Reformat TSV columns.

    `python3 -m scripts.tsv.reformat_columns -r tsv-data/`

6. Create splits.

    `python3 -m scripts.tsv.split tsv-data/ training-data/`

7. Generate statistics.

    `python3 -m scripts.statistics training-data/ statistics/`

## Duplicates
When creating splits for the first time, you will want to check for duplicates.
This is a manual process as you may want to experiment with the threshold parameters.

`python3 -m scripts.tsv.find_duplicates tsv-data/[dataset name here]`

Once you are satisfied, add the duplicates json to `[dataset].splits.json` and group them in the same split:

`python3 -m scripts.tsv.group_duplicates training-data/[dataset name here]/[dataset].splits.json`

Lastly, resplit the dataset as in step 6:

`python3 -m scripts.tsv.split tsv-data/ training-data/`