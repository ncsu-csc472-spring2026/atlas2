#!/usr/bin/env bash 

# Helper script for theHarvester for use in the ATLAS2 project
# Takes an input harvester file and outputs a formatted semicolon-separated
# file with the following structure:
#
# IP;Organization that owns IP's Block;Ping status;Domains Associated (comma-separated)

minArgs=2
maxArgs=4

# Checks for help flag and the right number of args
if [[ "$1" == "-h" || $# -lt $minArgs || $# -gt $maxArgs ]]; then
	echo -e "Usage: harvesthelper (-h) (-i) (-s) [PSU ID NUMBER OR NAME] [INPUT HARVESTER FILE]\n   Outputs to [PSU ID NUMBER OR NAME]_helper.txt\n   -h: Prints this help screen and exits\n   -i: Outputs list of IPs to [PSU ID NUMBER OR NAME]_ips.txt\n   -s: Outputs list of subdomains to [PSU ID NUMBER OR NAME]_subdomains.txt"
	exit 1
fi

psuNameArg=${@: -2:1}
harvesterArg=${@: -1}

# Checks to make sure the input file exists
(cat $harvesterArg > /dev/null 2> /dev/null)
if [ $? -eq 1 ]; then
	echo "$harvesterArg: No such file"
	exit 1
fi

# Creates the output file variable from the supplied PSU ID or name
helperOutput="${psuNameArg}_helper.txt"
(rm $helperOutput > /dev/null 2> /dev/null) # Removed old output file if it's there

ipOutput="${psuNameArg}_ips.txt"
(rm $ipOutput > /dev/null 2> /dev/null) # Removed old output file if it's there

subdomainsOutput="${psuNameArg}_subdomains.txt"
(rm $subdomainsOutput > /dev/null 2> /dev/null) # Removed old output file if it's there
subdomainsString=""

# Gets the list of IPs from the harvester output file using grep and an IP regex pattern
ips=$(grep -Pe "^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$" $harvesterArg)

# For every IP in the IP list:
for ip in $ips; do
	org=`whois $ip | grep "Organization" | awk -F\: 'NR==1{gsub(/Organization:\s+/, ""); print}'` # Run whois on the IP and grab the Organization attribute

	# Attempt to ping the IP to see if it's up or down
	(ping -c 1 -W 0.5 $ip > /dev/null 2> /dev/null)
	if [ $? -eq 0 ]; then
    		ping="UP"
	else
    		ping="DOWN"
	fi

	# If the -i flag is set, output the IP to the IP output file, separated by newlines
	if [[ "$1" == "-i" || "$2" == "-i" ]]; then
		(echo $ip >> $ipOutput)
	fi

	# Grab list of domains associated with the IP into a comma-separated list
	domains=$(grep "[:,]$ip" $harvesterArg | awk -F: '{print $1}' | paste -sd,)

	# If -s flag is set, put the list of subdomains found for this IP in the subdomainsString variable, separated by newlines
	if [[ "$1" == "-s" || "$2" == "-s" ]]; then
		subdomainsString="${subdomainsString}\n$(grep "[:,]$ip" $harvesterArg | awk -F: '{print $1}' | paste -s --delimiters='\n')"
	fi

	# Output into the helperOutput
	echo "$ip;$org;$ping;$domains" >> $helperOutput
done

# If the -s flag is set, output the variable holding all of the subdomains to the output file and strip all blank lines
if [[ "$1" == "-s" || "$2" == "-s" ]]; then
	(echo -e "$subdomainsString" | sort -u > $subdomainsOutput)
	(sed -i '/^\s*$/d' $subdomainsOutput)
fi

exit 0 # Exit success

