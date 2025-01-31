# galahad-corpus-data

### GaLAHaD-related Repositories
- [galahad](https://github.com/INL/galahad)
- [galahad-train-battery](https://github.com/INL/galahad-train-battery)
- [galahad-taggers-dockerized](https://github.com/INL/galahad-taggers-dockerized)
- [galahad-corpus-data](https://github.com/INL/galahad-corpus-data/) [you are here]
- [int-pie](https://github.com/INL/int-pie)
- [int-huggingface-tagger](https://github.com/INL/int-huggingface-tagger)
- [galahad-huggingface-models](https://github.com/INL/galahad-huggingface-models)

This repository contains the gold standard data for tagging and lemmatization developed in the CLARIAH-PLUS project.
The datasets are pos-tagged according to the [TDN (Tagset voor Diachroon corpusmateriaal van het Nederlands) guidelines](https://ivdnt.org/wp-content/uploads/2024/11/TDNV2_combi.pdf); and lemmatized according to the [Lemmatiseerprincipes voor GiGaNT, het centrale lexicon van het INT guidelines](https://ivdnt.org/wp-content/uploads/2024/11/lemmatiseerprincipesV2_combi.pdf).

The repository currently only publishes a tab-separated format with four columns: *token*, *pos*, *lemma* and *group_id*.
The last column requires some explanation; it is used to indicate that for instance the two tokens of *te rugghe* are considered a single word:

```
te	ADV(type=reg)	terug	mw_184982
rugghe	ADV(type=reg)	terug	mw_184982
```  

The *group_id* column is also used to link the parts of proper nouns and separable verbs (which may be discontinuous):
```
De      NOU-P   De Wilde        mw_217988
Wilde   NOU-P   De Wilde        mw_217988
was     VRB(finiteness=fin,tense=past)  zijn    
beter   AA(degree=comp,position=free)   beter   
en      CONJ(type=coor) en      
stondt  VRB(finiteness=fin,tense=past)  opstaan mw_974168
op      VRB(finiteness=fin,tense=past)  opstaan mw_974168         
ende    CONJ(type=coor) en      
nam     VRB(finiteness=fin,tense=past)  innemen mw_113851
een     PD(type=indef,subtype=art,position=prenom)      een     
purgatie        NOU-C(number=sg)        purgatie        
in      VRB(finiteness=fin,tense=past)  innemen mw_113851 
```

# Training data
Data in `training-data/` is tsv only and ready to be used by [galahad-train-battery](https://github.com/INL/galahad-train-battery). The files should not have column headers, so they can be merged by simply appending them. The files are partitioned in train, dev and test sets. In `*.partitionInformation.json`, the sources of the partitions are described.

# Datasets.json
`datasets.json` contains information about all public corpora and datasets that can be found in Galahad. Example usage:
```json
[{
    // An automated tool could read this path.
    "path": "training-data/letters-as-loot",
    // Columns as they appear in the tsv files at the path.
    "columns": [
        "token",
        "pos",
        "lemma",
        "group_id"
    ],
    "name": "letters-as-loot",
    "eraFrom": "1600",
    "eraTo": "1800",
    "tagset": "TDN-Core",
    // Source of the dataset
    "sourceName": "letters-as-loot",
    "sourceURL": "https://brievenalsbuit.ivdnt.org/",
    "version": "1.0.0",
    "description": "Letters as Loot (selection)"
},
{...} // Etc.
]
```
The real file cannot contain comments because json does not support that by default.

# Combinations
In `combinations/*.json` some useful combinations of datasets are predefined. Example:

```json
[{
    "name": "1600-1900",
    "description": "All datasets between 1600-1900 combined",
    "datasets": [
        "dbnl-excerpts-17",
        "dbnl-excerpts-18",
        "dbnl-excerpts-19",
        "dictionary-quotations-17",
        "dictionary-quotations-18",
        "dictionary-quotations-19",
        "couranten",
        "letters-as-loot"
    ] 
    // For other metadata like versioning, source and tagset
    // the respective datasets.json metadata is the ground truth. Let's not repeat ourselves.
    // This file is merely a suggestion of what to combine.
},
{...} // Etc.
]
```
