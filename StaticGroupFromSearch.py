#!/usr/bin/env python
import argparse
import csv
import getpass
import logging
import os
import posixpath
import sys
try:
    import xml.etree.cElementTree as Et
except ImportError:
    import xml.etree.ElementTree as Et
import urlparse

import requests


__help__ = """Example usage:
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Contains 'iPhone'" -u 'user' -p 'pass' --mobiledevices -s '*iPhone*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Starts with 'admin'" --computers --search 'admin*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Devices from list" --mobiledevices --csv-file /path/to/list.csv
"""


class Arguments(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="StaticGroupFromSearch",
            description="Use the '/match' endpoint for Computers and Mobile devices to generate Static Groups.",
            formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__help__)

        parser.add_argument('jssurl', type=str, default=None, help="JSS URL")
        parser.add_argument('groupname', type=str, default=None, help="new static group name")

        groupSearchType = parser.add_mutually_exclusive_group(required=True)
        groupSearchType.add_argument('-c', '--computers', action="store_true", help="search computers")
        groupSearchType.add_argument('-m', '--mobiledevices', action="store_true", help="search mobile devices")

        groupSearchInput = parser.add_mutually_exclusive_group(required=True)
        groupSearchInput.add_argument('-f', '--csv-file', type=str, dest='file', default=None,
                                      help="read search values from csv file")
        groupSearchInput.add_argument('-s', '--search', type=str, default=None, help="search for a value")

        parser.add_argument('-u', '--username', dest='username', type=str, default=None, help="API username")
        parser.add_argument('-p', '--password', dest='password', type=str, default=None, help="API user password")
        
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)
            
        args = parser.parse_args()

        self.searchtype = "computers" if args.computers else "mobiledevices"

        if args.search:
            self.searchvalue = [args.search]
        else:
            self.searchvalue = []
            with open(args.file, 'rU') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.searchvalue.append(row[0])
                    
        self.jssurl = self.clean_url(args.jssurl)
        self.groupname = args.groupname

        self.username = args.username if args.username else str(raw_input("API Username: "))
        self.password = args.password if args.password else getpass.getpass("API Password: ")

    @staticmethod
    def clean_url(url):
        # Replace with 'urlparse'
        cleaned_url = url.rstrip('/')
        if not (cleaned_url.startswith('http://') or cleaned_url.startswith('https://')) :
            print("valid prefix for server url not found: prefixing with https://")
            cleaned_url = 'https://' + cleaned_url

        return cleaned_url


class JamfProClient(object):
    """Class for interacting with the Jamf Pro API."""
    def __init__(self, url, username, password, matchtype):
        self._session = requests.Session()
        self._session.auth = (username, password)

        self.url = posixpath.join(url, 'JSSResource')

        if matchtype not in ('computers', 'mobiledevices'):
            raise Exception

        self.match_endpoint = '{0}/match'.format(matchtype)

        if matchtype == 'computers':
            self.group_endpoint = 'computergroups/id/0'
        else:
            self.group_endpoint = 'mobiledevicegroups/id/0'

    @staticmethod
    def _raise_exception(response):
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            if response.status_code == 409:
                print("A conflict with an existing group was encountered")
            else:
                print("an error occurred during the search: {0}".format(
                    error.message))
                print("check the URL used and try again\n")

            sys.exit(1)
        
    def get_match(self, searchvalue):
        print("performing search on the JSS at: ..{0}/{1}".format(self.match_endpoint, searchvalue))
        resp = self._session.get(
            posixpath.join(self.url, self.match_endpoint, searchvalue),
            headers={'Accept': 'text/xml'}
        )
        self._raise_exception(resp)
        return Et.fromstring(resp.text.encode('utf-8'))
    
    def create_group(self, postdata):
        print("creating new Static Group on the JSS at: ..{0}".format(self.group_endpoint))
        resp = self._session.post(
            posixpath.join(self.url, self.group_endpoint),
            headers={'Content-Type': 'text/xml'},
            data=postdata
        )
        return Et.fromstring(resp.text).findtext('id')


def CreateGroupPostData(input, collection, grouping, item, groupname):
    """this function reads computer IDs from the 'input' and returns XML for a POST"""
    root = Et.Element(collection)
    name = Et.SubElement(root, 'name')
    name.text = groupname
    is_smart = Et.SubElement(root, 'is_smart')
    is_smart.text = 'false'
    itemlist = Et.SubElement(root, grouping)
    
    for i in input:
        add_element = Et.SubElement(itemlist, item)
        add_element_id = Et.SubElement(add_element, 'id')
        add_element_id.text = i
        
    return Et.tostring(root)


def main():
    args = Arguments()
    print(args.searchvalue, args.groupname, args.searchtype)

    jamf = JamfProClient(args.jssurl, args.username, args.password, args.searchtype)
    
    if args.searchtype == 'computers':
        collection = 'computer_group'
        grouping = 'computers'
        item = 'computer'
    else:
        collection = 'mobile_device_group'
        grouping = 'mobile_devices'
        item = 'mobile_device'
    
    match_results = []
    for value in args.searchvalue:
        results = jamf.get_match(value)
        for result in results.findall(item):
            item_id = result.find('id').text
            if item_id not in match_results:
                match_results.append(item_id)
        
    size = len(match_results)
    if not size:
        print("the JSS matched no results to the provided search value\n")
        sys.exit(2)
    else:
        print("the JSS matched {0} result(s) to the provided search value".format(size))
        
    data = CreateGroupPostData(match_results, collection, grouping, item, args.groupname)
    new_group_id = jamf.create_group(data)

    print("the new Static Group has been created with ID: {0}\n".format(new_group_id))
    sys.exit(0)


if __name__ == '__main__':
    main()
