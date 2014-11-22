# Static Group from Search

## Description
---
This Python script performs a search on a JSS using the '/match' API endpoint for Computers or Mobile Devices and creates a Static Group of the result.

The script will take arguments and contains built-in help text.

## Usage
---
Script help text show here:

```
usage: StaticGroupFromSearch [-h] [-c | -m]
                             jssurl username password searchvalue groupname

Use the '/match' endpoint for Computers and Mobile devices to generate Static Groups.

positional arguments:
  jssurl               JSS URL
  username             API Username
  password             API User Password
  searchvalue          Search Value
  groupname            New Static Group Name

optional arguments:
  -h, --help           show this help message and exit
  -c, --computers      Search Computers
  -m, --mobiledevices  Search Mobile Devices

Example: $ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' 'admin*' "Starts with 'admin'" --computers
Example: $ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' 'iP*' "Starts with 'iP'" --mobildevices
```