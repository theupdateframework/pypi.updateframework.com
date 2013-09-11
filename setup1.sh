#!/bin/bash


# TODO:
# - OS-independent installation.


# Load shared environment variables.
source environment.sh


if [ -d $BASE_DIRECTORY/$QUICKSTART_DIRECTORY ]
then
  echo "Please run destroy.sh first!"; exit 1;
else
  mkdir $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  # Copy some scripts to the quickstart directory.
  cp quickstart.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cd $BASE_DIRECTORY
fi


# Download virtualenv.
if [ ! -d $VIRTUALENV_PACKAGE ]
then
  sudo apt-get install curl
  curl -O $VIRTUALENV_PATH$VIRTUALENV_PACKAGE.$PACKAGE_EXTENSION
  tar xvfz $VIRTUALENV_PACKAGE.$PACKAGE_EXTENSION
fi


# Create and activate our virtual environment.
if [ ! -d $VIRTUAL_ENVIRONMENT ]
then
  python $VIRTUALENV_PACKAGE/virtualenv.py $VIRTUAL_ENVIRONMENT
fi
source $VIRTUAL_ENVIRONMENT/bin/activate


# Install TUF and other required system packages.
# TODO: Conditional install.
sudo apt-get install expect libgmp-dev python-dev
pip install --upgrade $TUF_TARBALL


# Setup top-level roles.
cd $QUICKSTART_DIRECTORY

# Pass initially empty mirror directory to the quickstart script.
EMPTY_DIRECTORY=empty_directory
mkdir -p $EMPTY_DIRECTORY
./quickstart.sh $EMPTY_DIRECTORY

if [ $? -eq 0 ]
then
  rm -rf $EMPTY_DIRECTORY
  rm quickstart.sh
else
  echo "Could not create top-level TUF roles!"; exit 1;
fi
