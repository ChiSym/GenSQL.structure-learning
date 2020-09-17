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
 source venv/bin/activate
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
[docker-container]$ source venv/bin/activate
```

### Testing

In either, the docker container or the local virtual environment, run
```
make test
```
