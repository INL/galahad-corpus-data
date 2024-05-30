# GaLAHaD corpus data

This repository contains the gold standard data for tagging and lemmatization developed in the CLARIAH-PLUS project.
The datasets are pos-tagged and lemmatized according to the [TDN (Tagset voor Diachroon corpusmateriaal van het Nederlands) guidelines](https://ivdnt.org/wp-content/uploads/2021/05/TDN_INT_WP_1.pdf).

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

### GaLAHaD-related Repositories
- [galahad](https://github.com/INL/galahad)
- [galahad-train-battery](https://github.com/INL/galahad-train-battery)
- [taggers-dockerized](https://github.com/INL/taggers-dockerized)
- [galahad-corpus-data](https://github.com/INL/galahad-corpus-data/) [you are here]
- [int-pie](https://github.com/INL/pie) [a slightly modified version of the PIE tagger, will be released later]
- [int-huggingface-tagger](https://github.com/INL/huggingface-tagger) [will be released later]

# Training data
Data in `training-data/` is tsv only and ready to be used by [galahad-train-battery](https://github.com/INL/galahad-train-battery). The files should not have columns headers, so they can be merged by simply appending them.

<!---
# Source data
`source-data/` contains information about the source files of the data in `training-data/`.
-->

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
