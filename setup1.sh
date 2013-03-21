#!/bin/bash


# TODO:
# - OS-independent installation.


# Load shared environment variables.
source environment.sh


# Create necessary directories.
mkdir -p $BASE_DIRECTORY/$TUF_MIRROR_DIRECTORY
mkdir -p $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
# Copy some scripts to the quickstart directory.
cp quickstart.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY


cd $BASE_DIRECTORY


# Download virtualenv.
if [ ! -d $VIRTUALENV_PACKAGE ];
then
  apt-get install curl
  curl -O $VIRTUALENV_PATH$VIRTUALENV_PACKAGE.$PACKAGE_EXTENSION
  tar xvfz $VIRTUALENV_PACKAGE.$PACKAGE_EXTENSION
fi


# Create our virtual environment.
python $VIRTUALENV_PACKAGE/virtualenv.py $VIRTUAL_ENVIRONMENT
source $VIRTUAL_ENVIRONMENT/bin/activate


# Install TUF, expect.
# TODO: Conditional install.
pip install $TUF_TARBALL
apt-get install expect


cd $QUICKSTART_DIRECTORY


# Create top-level TUF roles.
# Pass mirror directory to the quickstart script.
./quickstart.sh $BASE_DIRECTORY/$TUF_MIRROR_DIRECTORY
if [ $? -eq 0 ];
then
  rm quickstart.sh
else
  echo "Could not create top-level TUF roles!"; exit 1;
fi
