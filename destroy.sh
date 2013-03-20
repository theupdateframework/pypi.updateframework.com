#!/bin/bash


# Load shared environment variables.
source environment.sh


# Destroy old directories.
# TODO: Confirmation!
rm -rf $BASE_DIRECTORY/$MIRROR_DIRECTORY
rm -rf $BASE_DIRECTORY/$QUICKSTART_DIRECTORY
