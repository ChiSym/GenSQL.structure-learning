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
VENV_LOCATION := venv
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

spn-repo:
ifneq ($(wildcard sum-product-dsl/.*),)
	@echo "Found sum-product-dsl repo. Will not download."
else
	@echo "Did not find sum-product-dsl repo. Will clone."
	git clone git@github.com:probcomp/sum-product-dsl.git
endif

spn: spn-repo
	${VENV_PIP} install ./sum-product-dsl

cgpm:
	${VENV_PIP} install git+https://github.com/probcomp/cgpm@20200908-schaechtle-experimenting-porting-to-python3

deps: spn cgpm
	${VENV_PIP} install -r requirements.txt
	@echo "Installed dependencies."

install: venv deps
	@mkdir -p ${ANALYSES_LOCATION}

###########################################################################
# Clean the house. CAVEAT: this removes the local copy of the sum-product-dsl.

clean:
	rm -rf ${VENV_LOCATION}
	rm -rf sum-product-dsl


###########################################################################
# Virtual Environment Setup

spn-test:
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m pytest --pyargs spn

cgpm-test:
	. ${VENV_LOCATION}/bin/activate && ${PYTHON} -m pytest --pyargs cgpm -k "not __ci_"

test: spn-test cgpm-test
