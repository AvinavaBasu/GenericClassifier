# generic-classifier

Identifies whether an organisation string is generic or specific

This codebase appears in the following project:

- [Improving generic classifier (2019)](https://confluence.cbsels.com/display/Electron/Improving+generic+classifier)

# Deployment

Make sure you have a directory called `models` under the project root and it contains
a model pickle file.

Build and test Dockerfile:

    docker build --tag generic-classifier:1.0 .
    docker run -it -p 8080:8080 --name gc generic-classifier:1.0
    # (inside docker container)
    serve &
    curl localhost:8080/ping
    curl --header "Content-Type: text/plain" -X POST --data $'Department of physics\nHarvard university' localhost:8080/invocations; echo

To test the API on a big payload, use:

    curl --header "Content-Type: text/plain" -X POST --data-binary @<INPUT_PATH> localhost:8080/invocations > <OUTPUT_PATH>

# Reproduction notes

All notebooks are run in a conda environment called `generic-classifier`, 
an export of which can be found in `environment.yml`.

Datasets are stored at `192.168.75.70:/home/m.le/generic-classifier/datasets`. 
Some derivative datasets are stored at `192.168.75.70:/home/m.le/generic-classifier/output`.
Please create the following folder structure:

    + some folder
    |--- datasets
    |---+ generic-classifier (project root)
    |   |--- output

# Running a classifier on a file

Refer "Usage" section under https://confluence.cbsels.com/display/Electron/2.+Final+proposal

To run a classifier on a file with affiliation xml element in each row, use the following template:

```
python3 processTaggedAffils.py [--model_path=path-to-model.pkl] <input-path> <output-path>
```

**Notice:** If you don't provide a model pickle file, the old system in `classifyGeneric.py` will be called.

# Structure of the code

The classifier as it was before Oct 2019: `classifyGeneric.py`

Files useful for productionization:

- `classifyGenericModified.py`: implementing the classifier
- `model.py`: feature extractors and custom transformers
- `processForImpactAnalysis.py`: processing affiliation strings in batch mode
- `utils.py`: miscellaneous utilities

Files useful for training:
- `notebooks/hyperparameter-tuning.ipynb`: train, evaluate and store models
- `notebooks/measure-performance-solution.ipynb`: evaluate
- `notebooks/extract-datasets.ipynb`: prepare datasets
"# GenericClassifier" 
