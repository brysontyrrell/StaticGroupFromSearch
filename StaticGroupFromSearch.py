#!/usr/bin/python
import argparse
import base64
import csv
import getpass
import httplib
import socket
import ssl
import sys
import urllib2
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


class TLS1Connection(httplib.HTTPSConnection):
    """Like HTTPSConnection but more specific"""
    def __init__(self, host, **kwargs):
        httplib.HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self):
        """Overrides HTTPSConnection.connect to specify TLS version"""
        # Standard implementation from HTTPSConnection, which is not
        # designed for extension, unfortunately
        sock = socket.create_connection((self.host, self.port),
                self.timeout, self.source_address)
        if getattr(self, '_tunnel_host', None):
            self.sock = sock
            self._tunnel()

        # This is the only difference; default wrap_socket uses SSLv23
        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)


class TLS1Handler(urllib2.HTTPSHandler):
    """Like HTTPSHandler but more specific"""
    def __init__(self):
        urllib2.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(TLS1Connection, req)


class ArgParser(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog = "StaticGroupFromSearch",
            description = "Use the '/match' endpoint for Computers and Mobile devices to generate Static Groups.",
            formatter_class=argparse.RawDescriptionHelpFormatter, epilog = """Example usage:
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Contains 'iPhone'" -u 'user' -p 'pass' --mobiledevices -s '*iPhone*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Starts with 'admin'" --computers --search 'admin*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com "Devices from list" --mobiledevices --csv-file /path/to/list.csv
            """)

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
            self.searchvalue = [urllib2.quote(args.search)]
        else:
            self.searchvalue = []
            with open(args.file, 'rU') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.searchvalue.append(urllib2.quote(row[0]))
                    
        self.jssurl = self.clean_url(args.jssurl)
        self.groupname = args.groupname

        self.username = args.username if args.username else str(raw_input("API Username: "))
        self.password = args.password if args.password else getpass.getpass("API Password: ")

    @staticmethod
    def clean_url(url):
        cleaned_url = url.rstrip('/')
        if not (cleaned_url.startswith('http://') or cleaned_url.startswith('https://')) :
            print("valid prefix for server url not found: prefixing with https://")
            cleaned_url = 'https://' + cleaned_url

        return cleaned_url


class JSS(object):
    def __init__(self, url, username, password, matchtype):
        self.auth = base64.b64encode(username + ':' + password)
        self.server = url
        self.match_endpoint = '/JSSResource/{0}/match/'.format(matchtype)
        if matchtype == 'computers':
            self.group_endpoint = '/JSSResource/computergroups/id/0'
        else:
            self.group_endpoint = '/JSSResource/mobiledevicegroups/id/0'
        
    def get_match(self, searchvalue):
        print("performing search on the JSS at: ..{0}{1}".format(self.match_endpoint, searchvalue))
        request = urllib2.Request(self.server + self.match_endpoint + searchvalue)
        return etree.fromstring(self.request(request))
    
    def create_group(self, postdata):
        print("creating new Static Group on the JSS at: ..{0}".format(self.group_endpoint))
        request = urllib2.Request(self.server + self.group_endpoint, postdata)
        request.get_method = lambda: 'POST'
        return etree.fromstring(self.request(request)).find('id').text

    def request(self, request):
        request.add_header('Authorization', 'Basic ' + self.auth)
        request.add_header('Content-Type', 'text/xml')
        request.add_header('Accept', 'text/xml')
        try:
            response = urllib2.urlopen(request)
        except ValueError as e:
            print("an error occurred during the search: {0}".format(e.message))
            print("check the URL used and try again\n")
            sys.exit(1)
        except urllib2.HTTPError as e:
            added_message = "there may be an existing group using the provided name\n" if e.code == 409 else ''
            print("an error occurred during the search: {0} {1}: {2}\n{3}".format(type(e).__name__, e.code, e.reason,
                                                                                  added_message))
            sys.exit(1)
        except urllib2.URLError as e:
            print("an error occurred during the search: {0}: {1}".format(type(e).__name__, e.reason))
            print("check the server URL used and try again\n")
            sys.exit(1)
        except Exception as e:
            print("an unknown error has occurred: {0}: {1}\n".format(type(e).__name__, e.message))
            sys.exit(1)

        return response.read()



def CreateGroupPostData(input, collection, grouping, item, groupname):
    """this function reads computer IDs from the 'input' and returns XML for a POST"""
    root = etree.Element(collection)
    name = etree.SubElement(root, 'name')
    name.text = groupname
    is_smart = etree.SubElement(root, 'is_smart')
    is_smart.text = 'false'
    itemlist = etree.SubElement(root, grouping)
    
    for i in input:
        add_element = etree.SubElement(itemlist, item)
        add_element_id = etree.SubElement(add_element, 'id')
        add_element_id.text = i
        
    return etree.tostring(root)


def main():
    args = ArgParser()

    urllib2.install_opener(urllib2.build_opener(TLS1Handler()))

    jss = JSS(args.jssurl, args.username, args.password, args.searchtype)
    
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
        results = jss.get_match(value)
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
    new_group_id = jss.create_group(data)

    print("the new Static Group has been created with ID: {0}\n".format(new_group_id))
    sys.exit(0)


if __name__ == '__main__':
    main()
