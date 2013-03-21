#!/usr/bin/env expect


# We use the venerable expect to drive signercli.py.
# https://en.wikipedia.org/wiki/Expect


# Get keystore, bit_length, password from the arguments to this script.
set keystore_directory [lindex $argv 0]
set key_size [lindex $argv 1]
set target_key_password [lindex $argv 2]
# Set expect timeout to N seconds.
set timeout 2


spawn signercli.py --genrsakey $keystore_directory
expect ".*Enter the number of bits for the RSA key.*:"
send "$key_size\r"


expect ".*Enter a password to encrypt the generated RSA key.*:"
send "$target_key_password\r"
expect ".*Confirm*:"
send "$target_key_password\r"


expect ".*Done."
