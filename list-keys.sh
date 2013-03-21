#!/usr/bin/env expect


# We use the venerable expect to drive signercli.py.
# https://en.wikipedia.org/wiki/Expect


# Get keystore, metadata_directory from the arguments to this script.
set keystore [lindex $argv 0]
set metadata_directory [lindex $argv 1]
# Set expect timeout to N seconds.
set timeout 2


spawn signercli.py --listkeys $keystore
expect ".*Enter the metadata directory.*:"
send "$metadata_directory\r"


expect ".*Listing the keyids in.*"
