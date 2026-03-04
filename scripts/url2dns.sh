#!/usr/bin/env bash

# Returns only A IP address records for all hostnames in a file passed in arg1.

(dig -f $1 +short | grep -P "^([0-9]+\.?){4}$" | sort | uniq)

exit 0
