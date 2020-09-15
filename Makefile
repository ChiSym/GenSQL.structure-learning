###########################################################################
# Command Variables
#
# These are usually not overridden by users but can be.
#
PYTHON ?= python3.6
PIP ?= pip3

###########################################################################
# Miscellaneous Variables
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

spn-repo:
ifneq ($(wildcard sum-product-dsl/.*),)
	@echo "Found sum-product-dsl repo. Will not download."
else
	@echo "Did not find sum-product-dsl repo. Will clone."
	git clone git@github.com:probcomp/sum-product-dsl.git
endif

spn: spn-repo
	${VENV_PIP} install ./sum-product-dsl

deps: spn
	@echo "Installed dependencies."

install: venv deps
	@mkdir -p ${ANALYSES_LOCATION}

clean:
	rm -rf ${VENV_LOCATION}
	rm -rf sum-product-dsl
