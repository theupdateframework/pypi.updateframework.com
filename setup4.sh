#!/bin/bash


# Load shared environment variables.
source environment.sh


# Our own global variables.
KEYSTORE_DIRECTORY=./keystore
REPOSITORY_DIRECTORY=./repository
REPOSITORY_CONFIGURATION_FILE=$REPOSITORY_DIRECTORY/config.cfg
REPOSITORY_METADATA_DIRECTORY=$REPOSITORY_DIRECTORY/metadata


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
  cp make-release.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp make-timestamp.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cd $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
fi


# FIXME: We are burdened to know the password from the previous step.
./make-release.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY $REPOSITORY_CONFIGURATION_FILE "release"
if [ $? -eq 0 ]
then
  ./make-timestamp.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY $REPOSITORY_CONFIGURATION_FILE "timestamp"
  if [ $? -eq 0 ]
  then
    # Copy files from the TUF repository to a designated WWW-accessible directory.
    # TODO: rsync, not just copy!
    cp -r $REPOSITORY_DIRECTORY/* $BASE_DIRECTORY/$TUF_MIRROR_DIRECTORY/
    rm make-release.sh make-timestamp.sh
  else
    echo "Could not make a new timestamp!"; exit 1;
  fi
else
  echo "Could not make a new release!"; exit 1;
fi
