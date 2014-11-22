# Static Group from Search

## Description
---
This Python script performs a search on a JSS using the '/match' API endpoint for Computers or Mobile Devices and creates a Static Group of the results.

The script takes arguments and contains built-in help text.

## Usage
---
A single phrase can be passed as the search criteria or a list provided in CSV format.  Any searchable criteria for an inventory record can be used along with wild card values (*).

CSV lists can contain a mix of values such as usernames, email addresses, serial numbers, MAC addresses, etc.  Your CSV file should be formated as a single column without a header:

| value1 |
|--------|
| value2 |
| value3 |

Passing an asterisk (*) as the criteria will return all device records.

## Help Text
---

Script help text show here:

```
usage: StaticGroupFromSearch [-h] (-c | -m) (-f FILE | -p PHRASE)
                             jssurl username password groupname

Use the '/match' endpoint for Computers and Mobile devices to generate Static Groups.

positional arguments:
  jssurl                JSS URL
  username              API username
  password              API user password
  groupname             new static group name

optional arguments:
  -h, --help            show this help message and exit
  -c, --computers       search computers
  -m, --mobiledevices   search mobile devices
  -f FILE, --csv-file FILE
                        read values from csv file
  -p PHRASE, --phrase PHRASE
                        search for a value

Example usage:
$ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' "Starts with 'admin'" --computers --phrase 'admin*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' "Contains 'iP'" --mobildevices --phrase '*iP*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' "Devices from list" --mobildevices --csv-file /path/to/list.csv
```