#!/usr/bin/env expect


# We use the venerable expect to drive quickstart.py.
# https://en.wikipedia.org/wiki/Expect


# Get project directory from the first argument to this script.
set project [lindex $argv 0]
# Set expect timeout to N seconds.
set timeout -1


spawn quickstart.py --project=$project
expect "When would you like your \"root.txt\" metadata to expire? (mm/dd/yyyy):"
# TODO: Compute a year from now().
send "08/31/2014\r"


expect "Enter the desired threshold for the role 'root':"
send "1\r"
expect "Enter a password for 'root' (1):"
send "root\r"
expect "Confirm:"
send "root\r"


expect "Enter the desired threshold for the role 'targets':"
send "1\r"
expect "Enter a password for 'targets' (1):"
send "targets\r"
expect "Confirm:"
send "targets\r"


expect "Enter the desired threshold for the role 'release':"
send "1\r"
expect "Enter a password for 'release' (1):"
send "release\r"
expect "Confirm:"
send "release\r"


expect "Enter the desired threshold for the role 'timestamp':"
send "1\r"
expect "Enter a password for 'timestamp' (1):"
send "timestamp\r"
expect "Confirm:"
send "timestamp\r"


expect "Successfully created the repository."
wait
