#!/bin/bash


# Load shared environment variables.
source environment.sh


# Create necessary directories.
mkdir -p $BASE_DIRECTORY/$MIRROR_DIRECTORY
mkdir -p $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
# Copy some scripts to the quickstart directory.
cp quickstart.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
cp create-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY


# Download virtualenv.
cd $BASE_DIRECTORY
if [ ! -d $VIRTUALENV_PACKAGE ];
then
  curl -O $VIRTUALENV_PATH$VIRTUALENV_PACKAGE.$PACKAGE_EXTENSION
  tar xvfz $VIRTUALENV_PACKAGE.$PACKAGE_EXTENSION
fi


# Create our virtual environment.
python $VIRTUALENV_PACKAGE/virtualenv.py virtual_python
source virtual_python/bin/activate


# Install TUF, expect.
# TODO: Conditional install.
pip install $TUF_TARBALL
sudo apt-get install expect


cd $QUICKSTART_DIRECTORY


# Create top-level TUF roles.
# Pass mirror directory to the quickstart script.
./quickstart.sh $BASE_DIRECTORY/$MIRROR_DIRECTORY
if [ $? -eq 0 ];
then
  rm $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/quickstart.sh
else
  echo "Could not create top-level TUF roles!"; exit 1;
fi


# Create keys for delegated target roles.
# Pass keystore, bit_length, password to the script to create key.
# TODO: Walk over PyPI directory tree to derive these roles.
./create-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/keystore 2048 simple
./create-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/keystore 2048 packages
./create-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/keystore 2048 source
./create-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/keystore 2048 D
./create-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/keystore 2048 Django


if [ $? -eq 0 ];
then
  rm $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/create-keys.sh
else
  echo "Could not create keys for delegated target roles!"; exit 1;
fi
