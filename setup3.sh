#!/bin/bash


# NOTES:
# - See the quotation marks around certain variables? They are very important
# for correctly passing quoted Python package names containing spaces.


# Load shared environment variables.
source environment.sh


# Our own global variables.
KEY_SIZE=2048
KEYSTORE_DIRECTORY=keystore
REPOSITORY_DIRECTORY=repository
REPOSITORY_METADATA_DIRECTORY=$REPOSITORY_DIRECTORY/metadata
REPOSITORY_TARGETS_DIRECTORY=$REPOSITORY_DIRECTORY/targets


# Create key with keystore ($1), bit_length ($2), password ($3),
# then capture the 64-hex key name.
create_key () {
  # http://stackoverflow.com/a/2778096
  echo $(./gen-rsa-key.sh $1 $2 "$3" | grep "Generated a new key:" | grep -Po '[\da-f]{64}')
}


# Does rolename ($1) exist in our keystore? If so, get its key.
get_key() {
  echo $(./list-keys.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY | grep "'$1'" | grep -Po '[\da-f]{64}')
}


# Delegate from PARENT_ROLE_NAME ($1) to CHILD_ROLE_NAME ($2).
delegate_role () {
  local PARENT_ROLE_NAME
  local PARENT_ROLE_PASSWORD
  local CHILD_FILES_DIRECTORY
  local CHILD_KEY_NAME
  local CHILD_KEY_PASSWORD
  local CHILD_ROLE_NAME
  local FULL_ROLL_NAME
  local needs_delegation

  PARENT_ROLE_NAME=$1
  CHILD_ROLE_NAME=$2

  FULL_ROLL_NAME=$PARENT_ROLE_NAME/$CHILD_ROLE_NAME
  CHILD_FILES_DIRECTORY=$REPOSITORY_DIRECTORY/$FULL_ROLL_NAME
  CHILD_KEY_NAME=""

  # Simply for demonstration purposes, use predictable passwords for parent and
  # child. We use the basename of a role name as its password so that we may be
  # able to predict the password for roles that share the same keys.
  PARENT_ROLE_PASSWORD=$(basename $PARENT_ROLE_NAME)
  CHILD_KEY_PASSWORD="$CHILD_ROLE_NAME"

  # Assume that we do need to delegate from parent to child.
  needs_delegation=false

  # Does the expected role metadata exist?
  if [ -e $REPOSITORY_METADATA_DIRECTORY/$FULL_ROLL_NAME.txt ]
  then
    # The role exists, but has its metadata diverged from the data?
    ./metadata_matches_data.py $REPOSITORY_DIRECTORY --full_role_name "$FULL_ROLL_NAME"
    if [ $? -eq 1 ]
    then
      # Metadata has diverged from data, so we need a delegation.
      needs_delegation=true
    fi
  else
    # This role does not exist, so we need a delegation.
    needs_delegation=true
  fi

  # Do we need to delegate from parent to child?
  if $needs_delegation
  then
    # Is the parent in targets/packages/.+?
    if [[ $PARENT_ROLE_NAME =~ targets/packages/.+ ]]
    then
      # Is the parent in targets/packages/.+/.+?
      if [[ $PARENT_ROLE_NAME =~ targets/packages/.+/.+ ]]
      then
        # Does targets/simple/$CHILD_ROLE_NAME exist? If so, reuse its key.
        # In other words, we reuse the simple package key for all of its actual packages.
        # Warning: this depends on the simple metadata having been generated earlier.
        CHILD_KEY_NAME=$(get_key "targets/simple/$CHILD_ROLE_NAME")
      else
        # Does targets/packages/.*/$CHILD_ROLE_NAME exist? If so, reuse its key.
        # In other words, we are sharing the "first letter" keys across "Python versions".
        CHILD_KEY_NAME=$(get_key "targets/packages/.*/$CHILD_ROLE_NAME")
      fi
    fi

    # Do we have a target key yet?
    if [ -z $CHILD_KEY_NAME ]
    then
      # If not, generate a new key.
      CHILD_KEY_NAME=$(create_key $KEYSTORE_DIRECTORY $KEY_SIZE "$CHILD_KEY_PASSWORD")
    fi

    ./make-delegation.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY "$CHILD_FILES_DIRECTORY" $PARENT_ROLE_NAME $PARENT_ROLE_PASSWORD "$CHILD_ROLE_NAME" $CHILD_KEY_NAME "$CHILD_KEY_PASSWORD"
  fi
}


# Walk over PyPI subdirectory ($1) tree to derive the rest of the delegated roles.
# TODO: More efficient updates with metadata_matches_data.py?
walk_repository_targets_subdirectory () {
  local REPOSITORY_TARGETS_SUBDIRECTORY
  local delegator
  local delegatee

  REPOSITORY_TARGETS_SUBDIRECTORY=$1

  find -L $REPOSITORY_TARGETS_SUBDIRECTORY -type d | sort | while read DIRECTORY
  do
    # Replace $DIRECTORY with its relevant substring.
    DIRECTORY=${DIRECTORY#$REPOSITORY_DIRECTORY/}

    # Extract delegator and delegatee role names.
    delegator=$(dirname "$DIRECTORY")
    delegatee=$(basename "$DIRECTORY")

    delegate_role $delegator "$delegatee"
  done
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
  cp list-keys.sh $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
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
# Crucial for sharing keys that we first walk /simple, then /packages.
# TODO: Revoke target roles and their delegations if a catalogued package has been deleted.
walk_repository_targets_subdirectory $REPOSITORY_TARGETS_DIRECTORY/simple
walk_repository_targets_subdirectory $REPOSITORY_TARGETS_DIRECTORY/packages


if [ $? -eq 0 ]
then
  rm gen-rsa-key.sh list-keys.sh make-delegation.sh
else
  echo "Could not setup delegated target roles!"; exit 1;
fi
