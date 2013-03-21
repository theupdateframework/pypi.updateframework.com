#!/bin/bash


# Load shared environment variables.
source environment.sh


# Our own global variables.
KEY_SIZE=2048
KEYSTORE_DIRECTORY=./keystore
REPOSITORY_DIRECTORY=./repository
REPOSITORY_METADATA_DIRECTORY=$REPOSITORY_DIRECTORY/metadata


# Activate virtual environment.
if [ ! -d $BASE_DIRECTORY/$VIRTUALENV_PACKAGE ];
then
  echo "Please run setup1.sh first!"; exit 1;
else
  source $BASE_DIRECTORY/$VIRTUAL_ENVIRONMENT/bin/activate
fi


# Check for keystore.
if [ ! -d $BASE_DIRECTORY/$QUICKSTART_DIRECTORY/keystore ];
then
  echo "Please run setup1.sh first!"; exit 1;
else
  # Copy some scripts to the quickstart directory.
  cp gen-rsa-key.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp list-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp make-delegation.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cd $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
fi


role_exists () {
  # Does rolename ($1) exists in our keystore?
  echo $(./list-keys.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY | grep $1 -c)
}


create_key () {
  # Create key with keystore ($1), bit_length ($2), password ($3),
  # then capture the 64-hex key name.
  # http://stackoverflow.com/a/2778096
  echo $(./gen-rsa-key.sh $1 $2 $3 | grep "Generated a new key:" | grep -Po '[\da-f]{64}')
}


function delegate_role () {
  PARENT_ROLE_NAME=$1
  PARENT_ROLE_PASSWORD=$2
  TARGET_ROLE_NAME=$3

  if [ $(role_exists $PARENT_ROLE_NAME/$TARGET_ROLE_NAME) -eq 0 ];
  then
    # Create key with keystore, bit_length, password.
    TARGET_KEY_NAME=$(create_key $KEYSTORE_DIRECTORY $KEY_SIZE $TARGET_ROLE_NAME)
    TARGET_KEY_PASSWORD=$TARGET_ROLE_NAME
    TARGET_FILES_DIRECTORY=$REPOSITORY_DIRECTORY/$PARENT_ROLE_NAME/$TARGET_ROLE_NAME

    mkdir -p $TARGET_FILES_DIRECTORY
    ./make-delegation.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY $TARGET_FILES_DIRECTORY $PARENT_ROLE_NAME $PARENT_ROLE_PASSWORD $TARGET_ROLE_NAME $TARGET_KEY_NAME $TARGET_KEY_PASSWORD
  fi
}


# Create keys for delegated target roles, and setup target delegations.
# TODO: Walk over PyPI directory tree to derive these roles.


# Setup targets/simple
delegate_role targets targets simple
# Setup targets/packages
delegate_role targets targets packages


if [ $? -eq 0 ];
then
  rm gen-rsa-key.sh list-keys.sh make-delegation.sh
else
  echo "Could not create keys for delegated target roles!"; exit 1;
fi
