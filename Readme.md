# galahad-corpus-data

### GaLAHaD-related Repositories
- [galahad](https://github.com/INL/galahad)
- [galahad-train-battery](https://github.com/INL/galahad-train-battery)
- [taggers-dockerized](https://github.com/INL/taggers-dockerized)
- [galahad-corpus-data](https://github.com/INL/galahad-corpus-data/) [you are here]
- [int-pie](https://github.com/INL/pie)
- [int-huggingface-tagger](https://github.com/INL/huggingface-tagger)

# Training data
Data in `training-data/` is tsv only and ready to be used by [galahad-train-battery](https://github.com/INL/galahad-train-battery). There must not be any headers, such that these datasets can be merge by simply appending them.

# Source data
`source-data/` contains information about the source files of the data in `training-data/`.

# Datasets.json
`datasets.json` contains information about all public corpora and datasets that can be found in Galahad. Example usage:
```json
[{
    "sourcePath": "source-data/gysseling",
    "trainingPath": "training-data/gysseling",
    // Columns as they appear in the tsv files at trainingPath.
    "columns": [ 
        "token",
        "pos",
        "lemma"
    ],
    "name": "Gysseling",
    "eraFrom": 1200,
    "eraTo": 1300,
    "tagset": "Gysseling",
    // If true, this corpus will appear in Overview -> Datasets and in Annotate -> Corpora -> Public Corpora
    "dataset": true, 
    // If true, this corpus will appear in Annotate -> Corpora -> Public Corpora
    // You might want to make some corpora publicly available without polluting the lists of datasets.
    "public": true,
    "sourceName": "Corpus Gysseling",
    "sourceURL": "https://corpusgysseling.ivdnt.org/"
},
{...} // Etc.
]
```
The real file should not contain comments, though, because json does not support that by default.
