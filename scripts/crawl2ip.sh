#!/usr/bin/env bash

# Returns only A IP address records for all hostnames in a file passed in arg1.
(grep -Po "(?<=https?:\/\/)[^\/]*" $1 | sort | uniq | dig -f - A +short | grep -P "^([0-9]+\.?){4}$" | sort | uniq)

exit 0
