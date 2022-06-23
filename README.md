# inferenceql.auto-modeling 

This guide will help you use the IQL auto-modeling project to build your own CrossCat models. Once built, these models can be queried using a variety of interfaces. This guide starts with building a model from an example dataset. It then shows you how to build a model from a dataset you supply. And latter sections go into more detail about different backends for auto-modeling, various interfaces for querying models, and a number of other considerations.  

#### TABLE OF CONTENTS
- [Setup dependencies](#setup-dependencies)
- [Building your first model](#building-your-first-model)
- [Building a model with your own dataset](#building-a-model-with-your-own-dataset)
- [Model-building backends](#model-building-backends)
  - [CGPM](#cgpm)
  - [Loom and CGPM](#loom-and-cgpm)
  - [ClojureCat](#clojurecat)
  - [Streaming Inference](#streaming-inference)
- [Quality control plots](#quality-control-plots)
- [Using CrossCat models](#using-crosscat-models)
  - [Observable notebooks](#observable-notebooks-1)
  - [IQL Viz](#iql-viz-1)
  - [Jupyter notebooks](#jupyter-notebooks)
- [Using SPN models](#using-spn-models)
- [Misc](#misc)

## Setup dependencies 

### Configure GitHub SSH keys

Running inferenceql.auto-modeling involves fetching private repositories from GitHub over SSH. If you have not set up SSH to be able to connect to GitHub follow [these instructions](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh). If you have already configured SSH to connect to GitHub [test your SSH connection to GitHub](https://docs.github.com/en/github/authenticating-to-github/testing-your-ssh-connection).

Due to a bug upstream the InferenceQL build process _must_ use `ssh-agent` to access your SSH keys. To ensure that this is happens you must must remove any configuration settings that direct SSH to use files instead. Print out your SSH settings by running `cat ~/.ssh/config`. You may see an `IdentityFile` declaration, like this:

```
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_rsa
```

The line `IdentityFile ~/.ssh/id_rsa` tells SSH to use the key file `~/.ssh/id_rsa` when accessing the referenced host.

For each `IdentityFile` line first verify that the referenced key is already present in `ssh-agent`. For security reasons `ssh-agent` uses unique character sequences called "fingerprints" to uniquely identify keys it is managing. Run `ssh-keygen -l -f` on any files for which there is a `IdentityFile` declaration and make note of the fingerprint. The `*` portion is the fingerprint.

```
% ssh-keygen -l -f ~/.ssh/id_rsa
4096 SHA256:****************************************** user@host.com (RSA)
```

Next list the SSH keys `ssh-agent` is managing by running `ssh-add -l`. Verify that each of the fingerprints printed by `ssh-keygen -l -f` matches one of the fingerprints displayed by `ssh-add -l`. If any are missing [add them to the SSH agent](https://docs.github.com/en/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#adding-your-ssh-key-to-the-ssh-agent).

```
% ssh-add -l
4096 SHA256:****************************************** /Users/user/.ssh/id_rsa (RSA)
```

Next comment out the `IdentityFile` lines in `~/.ssh/config` by prepending them with `#`:

```
Host *
  AddKeysToAgent yes
  UseKeychain yes
  # IdentityFile ~/.ssh/id_rsa
```

Finally [test your SSH connection to GitHub](https://docs.github.com/en/github/authenticating-to-github/testing-your-ssh-connection) once more.

### Get dependencies

#### Java

You will need a version of Java, version 8 or above. 
[See this for more info](https://clojure.org/guides/getting_started#_dependencies).

You should be ok if either `java --version` runs, or the the $JAVA_HOME environment variable is set. Check the latter with `echo $JAVA_HOME`.

#### Python 3

You will need a version of Python 3. 

Try running `python3.9 --version`. If you don't get a Python version number back, you might need to install a version of Python3 or you may need to set a working alias for the Python executuable in the project's Makefile.   

#### Other depedencies 

We will need Clojure and Yarn. See the following pages for instructions.

[Clojure](https://clojure.org/guides/getting_started#_clojure_installer_and_cli_tools)

[Yarn](https://classic.yarnpkg.com/en/docs/install)

That's it. Those are all the dependencies we need.

### Get auto-modeling 

First we will get IQL auto-modeling repo and switch to the right branch.

```bash
git clone git@github.com:probcomp/inferenceql.auto-modeling.git

cd inferenceql.auto-modeling 
```

### Build a Python virtual-env

Run our makefile target which will create a new Python virtual environment and install all our Python dependencies in it. There are also some Javascript dependencies the get installed during this step.

Afterwards, we just need to activate our Python virtual environment. 

```bash
make intall

source .venv/bin/activate
```

Now we are ready to use the auto-modeling repo!

## Building your first model 

### Add a dataset 

Next, we will add the dataset we want to model. (NOTE: dataset has already been added for now)

We are going to be working with a dataset from a clinical trial that studied COVID-19 symptoms called Beat-19. 

```bash
mkdir data
wget [beat-19-url] > data/data.csv
```

### Run the auto-modeling pipeline

IQL auto-modeling is built around DVC (https://dvc.org/), a project that helps with version control of machine learning pipelines.

The steps for building a model are encoded as DVC pipelines (see `dvc.yaml`) All we have to do is run the pipeline and DVC takes care of the rest. 

From the root auto-modeling directory, we can run the following command to get a list of the pipeline stages and which files they will produce giving us an overview of the work that will be done to build the model.

```
dvc stage list
```

Now to run all of the pipelines execute the following.

``` 
dvc repro -f
```

### About the model

We can find our newly produced models at `data/xcat/` 

Each .edn file, `sample.0.edn`, `sample.1.edn`, etc. is a CrossCat model. Together they form an ensemble of CrossCat models. We can work with individual CrossCat models or work with the ensemble via an sum-product network (covered later). 

In addition, auto-modeling supports multiple backends for learning models. The backend we just used is CGPM. We will cover other backends later in this tutorial. 

### Quality control plots 

Before we use our model, how can we know it is any good? 

Auto-modeling produces 2 quality control apps for comparing simulated data produced by the model and the original observed data.

You can find them in `qc/app` folder. 

`qc-dashboard.html` shows comparisons between all combinations of columns, while `qc-splom.html` shows a scatter plot matrix of just numerical columns--the latter is not so interesting here as we only have one numerical column. 

These apps are fully contained in their respective html files, so they can be easily moved around or shared.

The premise of the qc-plots is following: if our model has truly learned the multi-variate distribution of the data then the marginal and pairwise-marginal distributions of simulations from the model should match those of the observed data. These qc-plots allow one to visually confirm this.

NOTE: The simulations you see in the QC plots are produced from the ensemble of CrossCat models via a sum-product network. For this reason, they should better reflect the true distribution of the data than any single CrossCat model. 

NOTE: The plots support a number of features including panning, zooming, cross-selection, and details on hover. There are also other options in the options menu. You can find more details in the QC section of this guide. 

### Querying the model 

To do this we will need IQL query. Fortunately, it is included as part of the IQL auto-modeling repo. We just need to start the IQL query command-line interface by specifying our dataset, model, and schema.

We will use just `sample.0.edn` model for now, but we could just as easily use the other models as well.

```bash
clj -M -m inferenceql.query.main -d data/data.csv -s data/schema.edn -m data/xcat/sample.0.edn
```

Now that the `iql>` prompt is showing, we can run iql queries. Try running some of the following queries. 

This one just shows the first 5 rows in the dataset.

```sql 
SELECT * FROM data LIMIT 5;
```

This shows the uncoditional probability of the first 5 trial participants' BMI values.

```sql 
SELECT bmi, (PROBABILITY DENSITY OF bmi UNDER model AS p) FROM data LIMIT 5;
```

Here are some more advanced queries. Note: The command-line interface currently does not support new-lines in queries. However, other related apps do, see the "other ways of using the model" section.

This following query gives us the probability of the first 5 trial participants' BMI values given other information about them: exercise, smoker. [It is a long string. Be sure to run all of it.]

```sql
SELECT bmi, exercise, smoker, (PROBABILITY DENSITY OF bmi UNDER model CONDITIONED BY exercise AND smoker AS p) FROM data LIMIT 5;
```

This following query simulates the BMI and health_status of 10 trial participants who do not exercises. 

```sql
SELECT * FROM (GENERATE bmi, health_status UNDER model CONDITIONED BY exercise="0") LIMIT 5
```

Try some queries of your own.

See [the reference](https://github.com/probcomp/inferenceql.query) for the IQL query language and the IQL query command-line interface. 

### Other ways of using the model 

We can also use model in other contexts. 

#### IQL Viz

IQL Viz allows you to query your model in a spreadsheet like UI. [See the project on Github](https://github.com/probcomp/inferenceql.viz). 

#### Observable notebooks

Many of the UI components from UI viz along with IQL query are available in a notebook format. 

See [this example](https://observablehq.com/d/a1cf7c842638a28a) built around the model we just produced. 

Your own datasets and models and can be swapped into this notebook.

## Building a model with your own dataset

The first step is to add a clean data directory with your own CSV.

For the root directory of the auto-modeling repository, perform the following.

```bash
# Remove the data dir if it exists.
rm -rf data

# Create a clean dat dir.
mkdir data

# Copy your data to the data folder. 
# Replace ~/data.csv with the path to your csv file.
cp ~/data.csv data/data.csv
```

### Dataset-related settings

There are a variety of settings in the `params.yaml` file in the auto-modeling root dir. The following might need to be changed depending on your dataset.

#### schema

Auto-modeling tries to guess the data types in your CSV. You can see which data types are guessed by running `dvc repro -f guess-schema` and then opening `data/schema.edn`.

If you want to manually set the data types for one or more columns you can do that in `schema` section in `params.yaml`.

#### nullify

This setting allows you to specify which string values will be considered as null values in your CSV. 

### Inference-related settings  

There are a number of settings in `params.yaml` file that allow you to control the inference process. See the section below on the CGPM backend for more details on these settings. 

### QC options

See the comments in the `qc` section of the `params.yaml` file for details on the various settings available for QC plots.

### Build your model

Now you are ready to build your model. At this point follow the same steps outlined for building a model from the Beat19 dataset found earlier in this document.

## Model-building backends

IQL Auto-modeling supports a number of model-building backends. The previous sections on model building used the default CGPM backend. We will provide some more background on the CGPM backend here and also provide information on using alternatives.

### Switching between backends

Each backend is encoded as a `yaml` file. When `dvc repro -f` is run, the YAML file for backend currently named `dvc.yaml` is run. To switch to a different backend, rename `dvc.yaml` to any temporary name. And rename the YAML file for the backend to you want to use to `dvc.yaml`.

### CGPM

#### Key points 
* Default backend 
* Written in Python 
* Robust 
* DVC YAML filename: `dvc.yaml`

#### Requirements
* Java 
* Python 3 
* Clojure
* Yarn

#### Settings
The following settings in `params.yaml` allow you to control the inferece process using the default backend, CGPM.

- `sample_count` — This lets you set the number of CrossCat models to learn, which together will comprise the ensemble.
- `cgpm > minutes` — The amount of time (minutes) to spend on inference. Use this setting or `cgpm > iterations` but not both.
- `cgpm > iterations` — The number CGPM interations to spend on inference. Use this setting or `cgpm > minutes` but not both.

#### Outputs 

The key artifacts produced are as follows.

##### Individual CrossCat models

In `data/xcat/`, you can find multiple CrossCat models. Each one is a `.edn` file named `sample.0.edn`, `sample.1.edn`, etc. Any one of these individual CrossCat models can be used in an Observable notebook or in the IQL Viz spreadsheet app.

##### Ensemble of CrossCat models

`data/sppl/merged.json` is a sum-product network representation of all of the individual CrossCat models merged together forming an ensemble. This file can be used by IQL Query to start an IQL query server. The query server can then respond to sum-product queries from both an Observable notebook and the IQL Viz spreadsheet app. This is covered in a latter section. 

### Loom and CGPM 

#### Key points 
* Loom used to learn structure
* CGPM used to learn hyper-parameters
* Loom is written in C with Python bindings
* Robust 
* DVC yaml filename: `dvc-loom.yaml`

#### Requirements
* Java 
* Python 3 
* Docker 
* Clojure
* Yarn

#### Setup
TODO: notes on getting the Docker image.

#### Settings
All the settings in `params.yaml` that apply to the CGPM backend also apply to the LOOM + CGPM backend. In addition, there are the following.

- `loom > extra_passes` — The number of extra inference passes to perform when learning structure.

#### Outputs 
The outputs produced are the same as those produced by the CGPM backend. Please see the ouputs section for that backend.

### ClojureCat 

#### Key points 
* Written in Clojure
* Usable from both the JVM and the browser (JS environments)
* Fewest requirements 
* Experimental
* DVC YAML filename: `dvc-clojurecat.yaml`

#### Requirements
* Java 
* Clojure
* Yarn
* Python (only the DVC dependency)

#### Settings
- `clojurecat > iterations` — This setting controls the amount of inference to perform.

#### Outputs 

We can find our newly produced CrossCat model at `data/xcat/model.edn`.

Unlike the CGPM and LOOM + CGPM backends. Only a single CrossCat model is produced, and there is no ensemble SPN produced.

### Streaming Inference

#### Key points 
* Experimental
* DVC YAML filename: `dvc-stream.yaml`

## Using CrossCat models

### Observable notebooks 

#### Key points
* Observable notebooks might be the simplest way to get started with querying a CrossCat model.
* A number of UI components from the standalone IQL Viz app have been extracted for use from Observable.

#### How to use
- Follow these steps
  - Open [this notebook](https://observablehq.com/d/a1cf7c842638a28a). TODO: replace this with a simpler starter notebook.
  - Open the file attachements menu.
  - Replace the following files with the respective files from the auto-modeling file tree.
    - `nullified.csv` -- `data/nullified.csv`
    - `model.edn` -- Any one of the CrossCat models in `data/xcat` such as `data/xcat/sample.0.edn` or `data/xcat/sample.1.edn`.
    - `schema.edn` -- `data/schema.edn`
  - Now, take a look at the example cells in the notebook to start querying your model.

### IQL Viz 

#### Key points
* IQL Viz is a stand-alone Javascript app based around a spreadsheet-like interface.
* It supports features not available in Observable notebooks yet.

#### How to use
- Follow these step.
  - Get the latest version of the project [here](https://github.com/probcomp/inferenceql.viz). 
  - Follow the instructions for compiling the app
  - Open the app
  - Click on the triple dot icon and select `Change dataset and model`
  - For the files requested, select the following from the auto-modeling file tree.
    - data -- `data/nullified.csv`
    - model -- Any one of the CrossCat models in `data/xcat` such as `data/xcat/sample.0.edn` or `data/xcat/sample.1.edn`.
    - schema -- `data/schema.edn`
  - Take a look at the browser console to confirm your model and dataset were loaded properly.
  - Now, you can enter queries in the main text box and run them. 

### Jupyter notebooks 

## Using SPN models
### Background on SPPL and SPN 
### Starting IQL Query with an SPN
### Querying on the command line 
### Starting a remote query server

## Misc 
### Notes on Python dependencies and M1-macs.
### Helpful DVC commands
