# Automated Bayesian Data Modeling with InferenceQL

This sets up a new Python3 environment with SPPL and CGPM running either locally
or using an Ubuntu-based Dockerfile.

## Requirements: 

- The installation relies on SSH keys setup since we are cloning the private sum-product-dsl repo.


## Running the sofware with locally.

To install run:
```
$ make install
````
and then activate the virtual environement.
```
 source .venv/bin/activate
```

### CAVEAT: Python version 3.6

If Python3.6 is not found users may have to edit line 6 in the Makefile or set a global alias for Python using
```
alias PYTHON=python3
```

### Jupyter access
```
$ make notebook
```


## Running the sofware with Docker
If a local install is not an option. Install via Docker.

### Create the docker image.
```
$ make docker-image
````
### Jupyter access
Run the docker container and start a Jupyter notebook server at port 8000.
```
$ make docker-container
```

### Shell access
Once the container is running we can open a shell inside the container, too.
This will help in case we don't want/need Jupyter access.
```
$ make docker-shell
[docker-container]$ source .venv/bin/activate
```

### Testing

In either, the docker container or the local virtual environment, run
```
make test
```

### Quality Control (QC) images

The DVC stages `qc-dashboard-image` and `qc-splom-image` produce pngs in the `qc/images/` folder.

These images can be used to verify model quality.

Vega-lite command line utilities (version 5) are needed to run these stages. Install them with this.

```bash
yarn install
```

### Quality Control (QC) apps

The DVC stages `qc-dashboard-app` and `qc-splom-app` produce standalone html files in the `qc/app/`
folder. Open them in a browser. These interactive vega-lite visualizations can be used to verify
model quality.
