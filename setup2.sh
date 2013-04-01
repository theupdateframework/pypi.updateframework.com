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

  # Do we not have bandersnatch?
  if [ ! -d bandersnatch ]
  then
    # Install and setup bandersnatch.
    sudo apt-get install mercurial
    hg clone https://bitbucket.org/ctheune/bandersnatch
    cd bandersnatch
    python bootstrap.py
    bin/buildout
    cd $BASE_DIRECTORY
  fi

  bandersnatch/bin/bsn-mirror -c bandersnatch.conf
fi
