###########################################################################
# Python env variables
#
# These are usually not overridden by users but can be.
#
PYTHON ?= python3.6
PIP ?= pip3

###########################################################################
# This is where analyses are saved.
#
ANALYSES_LOCATION = analyses

###########################################################################
# Virtual Environment Locations
#
# Should not really be changed
#
VENV_LOCATION := .venv
VENV_PYTHON := ${VENV_LOCATION}/bin/python
VENV_PIP := ${VENV_LOCATION}/bin/pip

###########################################################################
# Virtual Environment Setup

venv:
	@echo ${VENV_LOCATION}
	@mkdir ${VENV_LOCATION}
	${PYTHON} -m venv ${VENV_LOCATION}

###########################################################################
# Install automated modeling.

deps:
	${VENV_PIP} install -r requirements.txt
	@echo "Installed dependencies."

home-dir:
	@mkdir -p ${ANALYSES_LOCATION}

install: venv deps home-dir

###########################################################################
# Clean the house. CAVEAT: this removes the local copy of the sum-product-dsl.

clean:
	rm -rf ${VENV_LOCATION}
	rm -rf sum-product-dsl


###########################################################################
# Testing

sppl-test:
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m pytest --pyargs sppl

cgpm-test:
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m pytest --pyargs cgpm -k "not __ci_"

test: sppl-test cgpm-test

###########################################################################
# Docker setup

docker-image:
	docker build . -t inferenceql.automodeling

docker-container: home-dir
	docker run  --name iql_auto -v ${ANALYSES_LOCATION}:/analyses -p 8000:8000 -t inferenceql.automodeling

docker-shell:
	docker exec -it iql_auto bin/bash

docker-push:
	docker tag inferenceql.automodeling probcomp/inferenceql.automodeling:pre-alpha.v$(VERSION)
	docker push probcomp/inferenceql.automodeling:pre-alpha.v$(VERSION)

###########################################################################
# Start a Jupyter notebook

notebook:
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m jupyter notebook --ip 0.0.0.0 --port=8000 --no-browser --allow-root
