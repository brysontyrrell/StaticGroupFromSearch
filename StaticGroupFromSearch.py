#!/usr/bin/python
import argparse
import base64
import csv
import sys
import urllib2
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

class ArgParser:
    def __init__(self):
        parser = argparse.ArgumentParser(prog = "StaticGroupFromSearch", description = "Use the '/match' endpoint for Computers and Mobile devices to generate Static Groups.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog = """Example usage:
$ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' "Starts with 'admin'" --computers --phrase 'admin*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' "Contains 'iP'" --mobildevices --phrase '*iP*'
$ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' "Devices from list" --mobildevices --csv-file /path/to/list.csv
            """)
        groupSearchType = parser.add_mutually_exclusive_group(required=True)
        groupSearchType.add_argument('-c', '--computers', action = "store_true", help = "search computers")
        groupSearchType.add_argument('-m', '--mobiledevices', action = "store_true", help = "search mobile devices")
        groupSearchInput = parser.add_mutually_exclusive_group(required=True)
        groupSearchInput.add_argument('-f', '--csv-file', type = str, dest = 'file', default = None, help = "read values from csv file")
        groupSearchInput.add_argument('-p', '--phrase', type = str, default = None, help = "search for a value")
        #parser.add_argument('--insecure', action="store_true", help = "Allow insecure connections")
        parser.add_argument('jssurl', type = str, default = None, help = "JSS URL")
        parser.add_argument('username', type = str, default = None, help = "API username")
        parser.add_argument('password', type = str, default = None, help = "API user password")
        parser.add_argument('groupname', type = str, default = None, help = "new static group name")
        
        if len(sys.argv)==1:
            parser.print_help()
            sys.exit(1)
            
        args = parser.parse_args()
        self.type = None
        
        if args.computers:
            self.type = "computers"
        elif args.mobiledevices:
            self.type = "mobiledevices"
            
        if args.phrase:
            self.searchvalue = [urllib2.quote(args.phrase)]
        elif args.file:
            self.searchvalue = []
            with open(args.file, 'rU') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.searchvalue.append(urllib2.quote(row[0]))
                    
        self.jssurl = args.jssurl.rstrip('/')
        self.username = args.username
        self.password = args.password
        self.groupname = args.groupname


class JSS:
    def __init__(self, url, username, password, type):
        self.auth = base64.b64encode(username + ':' + password)
        self.match_endpoint = '{0}/JSSResource/{1}/match/'.format(url, type)
        if type == 'computers':
            self.group_endpoint = '{0}/JSSResource/computergroups/id/0'.format(url)
        else:
            self.group_endpoint = '{0}/JSSResource/mobiledevicegroups/id/0'.format(url)
        
    def get_match(self, searchvalue):
        request = urllib2.Request(self.match_endpoint + searchvalue)
        request.add_header('Authorization', 'Basic ' + self.auth)
        request.add_header('Content-Type', 'text/xml')
        print("performing search on the JSS at: {0}{1}".format(self.match_endpoint, searchvalue))
        try:
            response = urllib2.urlopen(request)
        
        except Exception as e:
            print("an error occurred during the GET: {0}".format(e.code))
            print(e.read())
            sys.exit(e.code)
        
        return etree.fromstring(response.read())
    
    def create_group(self, data):
        request = urllib2.Request(self.group_endpoint, data)
        request.add_header('Authorization', 'Basic ' + self.auth)
        request.add_header('Content-Type', 'text/xml')
        request.get_method = lambda: 'POST'
        print("creating new Static Group on the JSS at: {0}".format(self.group_endpoint))
        try:
            response = urllib2.urlopen(request)
        
        except Exception as e:
            print("an error occurred during the POST: {0}".format(e.code))
            print(e.read())
            sys.exit(e.code)
        
        groupid = etree.fromstring(response.read()).find('id').text
        return groupid


def CreateGroupPostData(input, collection, list, item, groupname):
    '''this function reads computer IDs from the 'input' and returns XML for a POST'''
    root = etree.Element(collection)
    name = etree.SubElement(root, 'name')
    name.text = groupname
    is_smart = etree.SubElement(root, 'is_smart')
    is_smart.text = 'false'
    itemlist = etree.SubElement(root, list)
    
    for i in input:
        add_element = etree.SubElement(itemlist, item)
        add_element_id = etree.SubElement(add_element, 'id')
        add_element_id.text = i
        
    return etree.tostring(root)


if __name__ == '__main__':
    args = ArgParser()
    jss = JSS(args.jssurl, args.username, args.password, args.type)
    
    if args.type == 'computers':
        collection = 'computer_group'
        list = 'computers'
        item = 'computer'
    else:
        collection = 'mobile_device_group'
        list = 'mobile_devices'
        item = 'mobile_device'
    
    print collection, list, item
    
    match_results = []
    for i in args.searchvalue:
        results = jss.get_match(i)
        for r in results.findall(item):
            id = r.find('id').text
            if id not in match_results:
                match_results.append(id)
        
    size = len(match_results)
    if not size:
        print("the JSS matched no results to the provided search value")
        sys.exit(2)
    else:
        print("the JSS matched {0} result(s) to the provided search value".format(size))
        
    data = CreateGroupPostData(match_results, collection, list, item, args.groupname)
    
    new_group_id = jss.create_group(data)
    print("the new Static Group has been created at ID: {0}".format(new_group_id))
    sys.exit(0)