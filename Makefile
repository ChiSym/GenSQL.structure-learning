###########################################################################
# Python env variables
#
# These are usually not overridden by users but can be.
#
PYTHON ?= python3.9
PIP ?= pip

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
	${VENV_PIP} install --upgrade pip

###########################################################################
# Install automated modeling.

deps:
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m pip --default-timeout=1000 install -r requirements.txt
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m pip --default-timeout=1000 install install sppl==1.2.1 --no-deps
	yarn install

	@echo "Installed dependencies."

home-dir:
	@mkdir -p ${ANALYSES_LOCATION}

install: venv deps home-dir

###########################################################################
# Clean the house. CAVEAT: this removes the local copy of the sum-product-dsl.

clean:
	rm -rf ${VENV_LOCATION}

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
	docker build -f docker/Dockerfile.notebook . -t inferenceql.automodeling

docker-container: home-dir
	docker run  --name iql_auto -v $(shell pwd)/${ANALYSES_LOCATION}:/home/jovyan/work -p 8888:8888 -t inferenceql.automodeling

docker-shell:
	docker exec -it iql_auto /bin/bash

docker-push:
	docker tag inferenceql.automodeling probcomp/inferenceql.automodeling:pre-alpha.v$(VERSION)
	docker push probcomp/inferenceql.automodeling:pre-alpha.v$(VERSION)

docker-clean:
	docker rm -f iql_auto
	docker rmi -f inferenceql.automodeling

###########################################################################
# Start a Jupyter notebook

notebook:
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m jupyter notebook --ip 0.0.0.0 --port=8000 --no-browser --allow-root
