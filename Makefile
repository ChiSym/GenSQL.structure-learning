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

install: venv
	@mkdir -p ${ANALYSES_LOCATION}

clean:
	rm -rf ${VENV_LOCATION}
