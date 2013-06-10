#!/usr/bin/env expect


# We use the venerable expect to drive signercli.py.
# https://en.wikipedia.org/wiki/Expect


# Get keystore, metadata_directory from the arguments to this script.
set keystore_directory [lindex $argv 0]
set repository_metadata_directory [lindex $argv 1]
set target_files_directory [lindex $argv 2]
set recursive_walk [lindex $argv 3]
set parent_role_name [lindex $argv 4]
set parent_role_password [lindex $argv 5]
set target_role_name [lindex $argv 6]
set target_key_name [lindex $argv 7]
set target_key_password [lindex $argv 8]
# Set expect timeout to N seconds.
set timeout -1


spawn signercli.py --makedelegation $keystore_directory
expect "Enter the metadata directory:"
send "$repository_metadata_directory\r"


expect "Enter the directory containing the delegated role's target files:"
send "$target_files_directory\r"


expect "Recursively walk the given directory? (Y)es/(N)o:"
send "$recursive_walk\r"


expect "Choose and enter the parent role's full name:"
send "$parent_role_name\r"


expect "Enter the password for $parent_role_name "
send "$parent_role_password\r"


expect "Enter the delegated role's name:"
send "$target_role_name\r"


expect "Enter the keyid or \"quit\" when done:"
send "$target_key_name\r"


expect "Enter the keyid's password:"
send "$target_key_password\r"


expect "Enter the keyid or \"quit\" when done:"
send "quit\r"


expect "Signing "
