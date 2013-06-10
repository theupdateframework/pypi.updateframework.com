#!/bin/bash


# NOTES:
# - See the quotation marks around certain variables? They are very important
# for correctly passing quoted Python package names containing spaces.


# Load shared environment variables.
source environment.sh


# Our own global variables.
KEY_LIST=keylist.txt
KEY_SIZE=2048
KEYSTORE_DIRECTORY=keystore
REPOSITORY_DIRECTORY=repository
REPOSITORY_METADATA_DIRECTORY=$REPOSITORY_DIRECTORY/metadata
REPOSITORY_TARGETS_DIRECTORY=$REPOSITORY_DIRECTORY/targets


# Associate key name ($1) with full roll name ($2).
cache_key () {
  local FULL_ROLE_NAME
  local CHILD_KEY_NAME

  CHILD_KEY_NAME=$1
  FULL_ROLE_NAME=$2

  # We silently discard a null $CHILD_KEY_NAME.
  # Is the $CHILD_KEY_NAME not null?
  if [ -n $CHILD_KEY_NAME ]
  then
    # TODO: *uniquely* record $FULL_ROLL_NAME
    echo "$CHILD_KEY_NAME $FULL_ROLL_NAME" >> $KEY_LIST
  fi
}


# Create key with keystore ($1), bit_length ($2), password ($3),
# then capture the 64-hex key name.
create_key () {
  # http://stackoverflow.com/a/2778096
  echo $(./gen-rsa-key.sh $1 $2 "$3" | grep "Generated a new key:" | grep -Po '[\da-f]{64}')
}


# Does rolename ($1) exist in our cached list of keys? If so, get its key.
# NOTE: We handle duplicates by caring about only the first matching role.
get_key() {
  echo $(grep -m 1 "$1" $KEY_LIST | grep -Po '^[\da-f]{64}')
}


# Delegate CHILD_FILES_DIRECTORY ($3) from PARENT_ROLE_NAME ($1) to
# CHILD_ROLE_NAME ($2).
delegate_role () {
  local CHILD_FILES_DIRECTORY
  local CHILD_KEY_NAME
  local CHILD_KEY_PASSWORD
  local CHILD_ROLE_NAME
  local FULL_ROLL_NAME
  local PARENT_ROLE_NAME
  local PARENT_ROLE_PASSWORD
  local RECURSIVE_WALK
  local needs_delegation

  PARENT_ROLE_NAME=$1
  CHILD_ROLE_NAME=$2
  CHILD_FILES_DIRECTORY=$3

  FULL_ROLL_NAME=$PARENT_ROLE_NAME/$CHILD_ROLE_NAME
  CHILD_KEY_NAME=""

  # Simply for demonstration purposes, use predictable passwords for parent and
  # child. We use the basename of a role name as its password so that we may be
  # able to predict the password for roles that share the same keys.
  PARENT_ROLE_PASSWORD=$(basename $PARENT_ROLE_NAME)
  CHILD_KEY_PASSWORD="$CHILD_ROLE_NAME"

  # Recursively walk the child files directory? (Y)es/(N)o
  RECURSIVE_WALK='Y'

  # Assume that we do need to delegate from parent to child.
  needs_delegation=false

  # Does the expected role metadata exist?
  if [ -e $REPOSITORY_METADATA_DIRECTORY/"$FULL_ROLL_NAME".txt ]
  then
    # The role exists, but has its metadata diverged from the data?
    ./metadata_matches_data.py $REPOSITORY_DIRECTORY --full_role_name "$FULL_ROLL_NAME"
    if [ $? -eq 1 ]
    then
      # Metadata has diverged from data, so we need a delegation.
      echo "Stale role: $FULL_ROLE_NAME"
      needs_delegation=true

      # Get key for extant role.
      CHILD_KEY_NAME=$(get_key "$FULL_ROLL_NAME")
      # Freak out if key is MIA.
      if [ -z $CHILD_KEY_NAME ]
      then
        echo "Key missing for extant role! => $FULL_ROLL_NAME"; exit 1;
      fi
    else
      # TODO: Handle abnormal exit from metadata_matches_data.py.
      echo "Fresh role: $FULL_ROLE_NAME"
    fi
  else
    # This role does not exist, so we need a delegation.
    echo "New role: $FULL_ROLE_NAME"
    needs_delegation=true

    # Generate and cache a new key.
    CHILD_KEY_NAME=$(create_key $KEYSTORE_DIRECTORY $KEY_SIZE "$CHILD_KEY_PASSWORD")
    cache_key $CHILD_KEY_NAME "$FULL_ROLE_NAME"
  fi

  # Do we need to delegate from parent to child?
  if $needs_delegation
  then
    # Do we have a child key yet?
    if [ -z $CHILD_KEY_NAME ]
    then
      echo "Key missing for making role delegation! => $FULL_ROLL_NAME"; exit 1;
    else
      # Proceed with delegation.
      ./make-delegation.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY "$CHILD_FILES_DIRECTORY" $RECURSIVE_WALK $PARENT_ROLE_NAME $PARENT_ROLE_PASSWORD "$CHILD_ROLE_NAME" $CHILD_KEY_NAME "$CHILD_KEY_PASSWORD"

      # Freak out on failure.
      if [ $? -ne 0 ]
      then
        echo "Delegation failed! => $FULL_ROLL_NAME"; exit 1;
      fi
    fi
  fi
}


# Activate virtual environment.
if [ ! -d $BASE_DIRECTORY/$VIRTUAL_ENVIRONMENT ]
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
  cp metadata_matches_data.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp gen-rsa-key.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp make-delegation.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cd $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
fi


# Check for PyPI.
if [ ! -d $BASE_DIRECTORY/$PYPI_MIRROR_DIRECTORY ]
then
  echo "Please run setup2.sh first!"; exit 1;
else
  # Create symbolic links to pypi.python.org subdirectories.
  ln -fs $BASE_DIRECTORY/$PYPI_MIRROR_DIRECTORY/web/simple/ $REPOSITORY_TARGETS_DIRECTORY
  ln -fs $BASE_DIRECTORY/$PYPI_MIRROR_DIRECTORY/web/packages/ $REPOSITORY_TARGETS_DIRECTORY
fi


# Create or update delegated target roles, or their delegations.
# By default, we delegate everything in PyPI from targets to targets/stable.
delegate_role targets stable $REPOSITORY_TARGETS_DIRECTORY
# TODO: Revoke target roles and their delegations if a catalogued package has been deleted.


if [ $? -eq 0 ]
then
  # We keep metadata_matches_data.py because it is a useful utility.
  rm gen-rsa-key.sh make-delegation.sh
else
  echo "Could not setup delegated target roles!"; exit 1;
fi
