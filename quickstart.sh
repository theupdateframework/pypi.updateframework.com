#!/usr/bin/env expect


# We use the venerable expect to drive quickstart.py.
# https://en.wikipedia.org/wiki/Expect


# Get project directory from the first argument to this script.
set project [lindex $argv 0]
# Set expect timeout to N seconds.
set timeout 2


spawn quickstart.py --project=$project --verbose=1
expect ".*When would you like your certificates to expire.*:"
# TODO: Compute a year from now().
send "12/01/2013\r"


expect ".*Enter the desired threshold for the role 'root':"
send "1\r"
expect ".*Enter a password for 'root' .*:"
send "root\r"
expect ".*Confirm:"
send "root\r"


expect ".*Enter the desired threshold for the role 'targets':"
send "1\r"
expect ".*Enter a password for 'targets' .*:"
send "targets\r"
expect ".*Confirm:"
send "targets\r"


expect ".*Enter the desired threshold for the role 'release':"
send "1\r"
expect ".*Enter a password for 'release' .*:"
send "release\r"
expect ".*Confirm:"
send "release\r"


expect ".*Enter the desired threshold for the role 'timestamp':"
send "1\r"
expect ".*Enter a password for 'timestamp' .*:"
send "timestamp\r"
expect ".*Confirm:"
send "timestamp\r"


expect ".*Successfully created the repository."
