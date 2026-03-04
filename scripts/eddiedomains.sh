#!/bin/bash

if [[ $# -lt 1 || $# -gt 3 ]]; then
	echo -e "Usage: ./eddiedomains.sh [-i] [input file] (output file)\n Prints the domain name of PSUs from a custom EDDIE report (output file is optional, prints to stdout by default) \n Options:\n -i: print the PSU ID along with the corresponding domain name"
	exit 1
fi

if [ $# == 1 ]; then
	cat $1 | grep -Po "(?<=\@)[A-z0-9]+(\.[A-z0-9]+)*" | sort -u 
elif [ $# -gt 1 ]; then
	if [[ "$1" == "-i" ]]; then
		if [[ $# == 2 ]]; then
			awk -F, '{print $6"@"$13}' $2 | awk -F\@ '{print $1,$3}' | grep -Po '[0-9][0-9A-Z]+\s+([A-z0-9\.\-\_]+)+' | sort -u
		elif [[ $# == 3 ]]; then
			awk -F, '{print $6"@"$13}' $2 | awk -F\@ '{print $1,$3}' | grep -Po '[0-9][0-9A-Z]+\s+([A-z0-9\.\_\-]+)+' | sort -u > $3
		fi

		exit 0
	elif [ $# == 2 ]; then
		cat $1 | grep -Po "(?<=\@)[A-z0-9\.\-\_]+([A-z0-9\.\-\_]+)*" | sort -u > $2
	fi
fi

