#!/bin/bash


# Load shared environment variables.
source environment.sh


# Our own global variables.
REPOSITORY_DIRECTORY=repository
REPOSITORY_TARGETS_DIRECTORY=$REPOSITORY_DIRECTORY/targets


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
  cp check.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp delegate.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp delegate_claimed_targets.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp delegate_recently_claimed_targets.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  cp delegate_unclaimed_targets.py $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
  # Switch to the quickstart directory.
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


# Create or update target delegators and delegatees.

# First, promote some "recently-claimed" delegations to the "claimed" role.
./delegate_claimed_targets.py

if [ $? -eq 0 ]
then
  # Preliminaries: "targets" is the set of all files on PyPI; "packages" are sets
  # of targets; "projects" are sets of packages.
  # Next, promote some projects to the "recently-claimed" role.
  ./delegate_recently_claimed_targets.py

  if [ $? -eq 0 ]
    # Finally, delegate all targets by default to the "unclaimed" role.
    ./delegate_unclaimed_targets.py
  then
      if [ $? -eq 0 ]
      then
        # Remove ancillary shell scripts.
        rm check.py
        rm delegate.py
        rm delegate_claimed_targets.py
        rm delegate_recently_claimed_targets.py
        rm delegate_unclaimed_targets.py
      else
        echo "Could not delegate unclaimed targets!"; exit 1;
      fi
  else
    echo "Could not delegate recently-claimed targets!"; exit 1;
  fi
else
  echo "Could not delegate claimed targets!"; exit 1;
fi


