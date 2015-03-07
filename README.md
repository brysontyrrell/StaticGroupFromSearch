# Static Group from Search

## Description
---
This Python script performs a search on a JSS using the '/match' API endpoint for Computers or Mobile Devices and creates a Static Group of the results.

The script takes arguments and contains built-in help text.

## Usage
---
A single phrase can be passed as the search criteria or a list provided in CSV format.  Any searchable criteria for an inventory record can be used along with wild card values (*).

CSV lists can contain a mix of values such as usernames, email addresses, serial numbers, MAC addresses, etc.  Your CSV file should be formatted as a single column without a header:

| value1 |
|--------|
| value2 |
| value3 |

Passing an asterisk (*) as the criteria will return all device records.

## Help Text
---

Script help text show here:

```
usage: StaticGroupFromSearch [-h] (-c | -m) (-f FILE | -s SEARCH)
                             [-u USERNAME] [-p PASSWORD]
                             jssurl groupname

Use the '/match' endpoint for Computers and Mobile devices to generate Static Groups.

positional arguments:
  jssurl                JSS URL
  groupname             new static group name

optional arguments:
  -h, --help            show this help message and exit
  -c, --computers       search computers
  -m, --mobiledevices   search mobile devices
  -f FILE, --csv-file FILE
                        read search values from csv file
  -s SEARCH, --search SEARCH
                        search for a value
  -u USERNAME, --username USERNAME
                        API username
  -p PASSWORD, --password PASSWORD
                        API user password

Example usage:
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Contains 'iPhone'" -u 'user' -p 'pass' --mobildevices -s '*iPhone*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Starts with 'admin'" --computers --search 'admin*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Devices from list" --mobildevices --csv-file /path/to/list.csv.csv
```