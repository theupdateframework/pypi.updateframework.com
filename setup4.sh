#!/bin/bash


# Load shared environment variables.
source environment.sh


# Activate virtual environment.
if [ ! -d $BASE_DIRECTORY/$VIRTUALENV_PACKAGE ]
then
  echo "Please run setup1.sh first!"; exit 1;
else
  source $BASE_DIRECTORY/$VIRTUAL_ENVIRONMENT/bin/activate
fi


# Check for keystore.
if [ ! -d $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/keystore ]
then
  echo "Please run setup1.sh first!"; exit 1;
else
  # Copy some scripts to the quickstart directory.
  cp check.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp delegate.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp make_release.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp make_timestamp.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cd $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
fi


# Update release.
./make_release.py

if [ $? -eq 0 ]
then
  # Update timestamp.
  ./make_timestamp.py
  if [ $? -eq 0 ]
  then
    # Remove ancillary shell scripts.
    rm check.py
    rm delegate.py
    rm make_release.py
    rm make_timestamp.py
  else
    echo "Could not make a new timestamp!"; exit 1;
  fi
else
  echo "Could not make a new release!"; exit 1;
fi


