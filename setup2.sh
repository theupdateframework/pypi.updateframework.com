#!/bin/bash


# Load shared environment variables.
source environment.sh


# Mirror PyPI.
if [ ! -d $BASE_DIRECTORY/$VIRTUAL_ENVIRONMENT ]
then
  echo "Please run setup1.sh first!"; exit 1;
else

  cp bandersnatch.conf $BASE_DIRECTORY
  cd $BASE_DIRECTORY
  source $VIRTUAL_ENVIRONMENT/bin/activate

  # Install bandersnatch.
  pip install --upgrade -r https://bitbucket.org/ctheune/bandersnatch/raw/stable/requirements.txt

  bandersnatch -c bandersnatch.conf mirror
fi
