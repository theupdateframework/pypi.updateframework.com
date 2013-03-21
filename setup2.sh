#!/bin/bash


# Load shared environment variables.
source environment.sh


cd $BASE_DIRECTORY


# Mirror PyPI.
if [ ! -d $VIRTUALENV_PACKAGE ];
then
  echo "Please run setup1.sh first!"; exit 1;
else
  source $VIRTUAL_ENVIRONMENT/bin/activate
  pip install --upgrade pep381client
  mkdir -p $PYPI_MIRROR_DIRECTORY
  cd $PYPI_MIRROR_DIRECTORY
  # If you run into trouble, goto http://bitbucket.org/loewis/pep381client/
  pep381run .
fi
