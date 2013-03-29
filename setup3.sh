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


# Does rolename ($1) exist in our keystore?
role_exists () {
  echo $(./list-keys.sh $KEYSTORE_DIRECTORY $REPOSITORY_METADATA_DIRECTORY | grep "'$1'" -c)
}


# Delegate from PARENT_ROLE_NAME ($1), with PARENT_ROLE_PASSWORD ($2),
# to CHILD_ROLE_NAME ($3).
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
  PARENT_ROLE_PASSWORD=$2
  CHILD_ROLE_NAME=$3
  CHILD_KEY_NAME=""
  CHILD_KEY_PASSWORD="$CHILD_ROLE_NAME"
  FULL_ROLL_NAME=$PARENT_ROLE_NAME/$CHILD_ROLE_NAME
  CHILD_FILES_DIRECTORY=$REPOSITORY_DIRECTORY/$FULL_ROLL_NAME

  # Assume that we do need to delegate from parent to child.
  needs_delegation=false

  # Is this a new role?
  if [ $(role_exists "$FULL_ROLL_NAME") -eq 0 ]
  then
    # Then we need a delegation.
    needs_delegation=true
  else
    # This is not a new role, but has its metadata diverged from the data?
    ./metadata_matches_data.py $REPOSITORY_DIRECTORY "$FULL_ROLL_NAME"
    if [ $? -eq 1 ]
    then
      # Metadata has diverged from data, so we need a delegation.
      needs_delegation=true
    fi
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
        CHILD_KEY_NAME=$(get_key "targets/simple/$CHILD_ROLE_NAME")
      else
        # Does targets/packages/.*/$CHILD_ROLE_NAME exist? If so, reuse its key.
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


list_directories(){
  # TODO: Find a command that preserves quotes,
  # while ignoring anything other than directories.
  ls $1
}


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
  ln -fs $BASE_DIRECTORY/$PYPI_MIRROR_DIRECTORY/web/simple/ $REPOSITORY_TARGETS_DIRECTORY/simple
  ln -fs $BASE_DIRECTORY/$PYPI_MIRROR_DIRECTORY/web/packages/ $REPOSITORY_TARGETS_DIRECTORY/packages
fi


# Create or update delegated target roles, or their delegations.
# Walk over PyPI directory tree to derive these roles.
# TODO: Revoke target roles and their delegations if a catalogued package has been deleted.


# targets -> targets/simple
delegate_role targets targets simple

# targets/simple -> targets/simple/$PACKAGE
# http://forums.fedoraforum.org/archive/index.php/t-166962.html
list_directories $REPOSITORY_TARGETS_DIRECTORY/simple | while read PACKAGE
do
  # FIXME: We are burdened to know the password from the previous step.
  delegate_role targets/simple simple "$PACKAGE"
done


# targets -> targets/packages
delegate_role targets targets packages

# targets/packages -> targets/packages/$PYTHON_VERSION
list_directories $REPOSITORY_TARGETS_DIRECTORY/packages | while read PYTHON_VERSION
do
  delegate_role targets/packages packages $PYTHON_VERSION

  # targets/packages/$PYTHON_VERSION -> targets/packages/$PYTHON_VERSION/$FIRST_LETTER
  list_directories $REPOSITORY_TARGETS_DIRECTORY/packages/$PYTHON_VERSION | while read FIRST_LETTER
  do
    delegate_role targets/packages/$PYTHON_VERSION $PYTHON_VERSION $FIRST_LETTER

    # targets/packages/$PYTHON_VERSION/$FIRST_LETTER -> targets/packages/$PYTHON_VERSION/$FIRST_LETTER/$PACKAGE
    list_directories $REPOSITORY_TARGETS_DIRECTORY/packages/$PYTHON_VERSION/$FIRST_LETTER | while read PACKAGE
    do
      delegate_role targets/packages/$PYTHON_VERSION/$FIRST_LETTER $FIRST_LETTER $PACKAGE
    done
  done
done


if [ $? -eq 0 ]
then
  rm metadata_matches_data.py gen-rsa-key.sh list-keys.sh make-delegation.sh
else
  echo "Could not setup delegated target roles!"; exit 1;
fi
