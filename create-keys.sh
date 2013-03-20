#!/usr/bin/env expect


# We use the venerable expect to drive signercli.py.
# https://en.wikipedia.org/wiki/Expect


# Get keystore, bit_length, password from the arguments to this script.
set keystore [lindex $argv 0]
set bit_length [lindex $argv 1]
set password [lindex $argv 2]
# Set expect timeout to N seconds.
set timeout 2


spawn signercli.py --genrsakey $keystore/
expect ".*Enter the number of bits for the RSA key*:"
send "$bit_length\r"


expect ".*Enter a password to encrypt the generated RSA key*:"
send "$password\r"
expect ".*Confirm*:"
send "$password\r"


expect ".*Done."
