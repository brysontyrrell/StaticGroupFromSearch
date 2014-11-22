#!/usr/bin/python
import argparse
import base64
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
            epilog = """Example: $ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' 'admin*' "Starts with 'admin'" --computers
Example: $ ./StaticGroupFromSearch.py https://jss.myorg.com 'user' 'pass' 'iP*' "Starts with 'iP'" --mobildevices
            """
            )

        groupSearchType = parser.add_mutually_exclusive_group()
        groupSearchType.add_argument('-c', '--computers', action = "store_true", help = "Search Computers")
        groupSearchType.add_argument('-m', '--mobiledevices', action = "store_true", help = "Search Mobile Devices")
        #parser.add_argument('--insecure', action="store_true", help = "Allow insecure connections")
        parser.add_argument('jssurl', type = str, default = None, help = "JSS URL")
        parser.add_argument('username', type = str, default = None, help = "API Username")
        parser.add_argument('password', type = str, default = None, help = "API User Password")
        parser.add_argument('searchvalue', type = str, default = None, help = "Search Value")
        parser.add_argument('groupname', type = str, default = None, help = "New Static Group Name")
        
        if len(sys.argv)==1:
            parser.print_help()
            sys.exit(1)
            
        args = parser.parse_args()
        self.type = None
        
        if args.computers:
            self.type = "computers"
        elif args.mobiledevices:
            self.type = "mobiledevices"
        
        if not self.type:
            print("""StaticGroupFromSearch: error: you must specify if you are searching '--computers' or '--mobiledevices'
                              see '--help' for more details
""")
            sys.exit(1)
            
        self.jssurl = args.jssurl.rstrip('/')
        self.username = args.username
        self.password = args.password
        self.searchvalue = urllib2.quote(args.searchvalue)
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



def CreateGroupPostData(input, type, groupname):
    '''this function reads computer IDs from the 'input' and returns XML for a POST
    the 'input' must be an ElementTree object'''
    if type == 'computers':
        collection = 'computer_group'
        list = 'computers'
        item = 'computer'
    else:
        collection = 'mobile_device_group'
        list = 'mobile_devices'
        item = 'mobile_device'
        
    root = etree.Element(collection)
    name = etree.SubElement(root, 'name')
    name.text = groupname
    is_smart = etree.SubElement(root, 'is_smart')
    is_smart.text = 'false'
    itemlist = etree.SubElement(root, list)
    
    for element in input.findall(item):
        add_element = etree.SubElement(itemlist, item)
        add_element_id = etree.SubElement(add_element, 'id')
        add_element_id.text = element.find('id').text
        
    return etree.tostring(root)


if __name__ == '__main__':
    args = ArgParser()
    jss = JSS(args.jssurl, args.username, args.password, args.type)
    match_results = jss.get_match(args.searchvalue)
    size = int(match_results.find('size').text)
    if not size:
        print("the JSS matched no retuls to the provided search value")
        sys.exit(2)
    else:
        print("the JSS matched {0} result(s) to the provided search value".format(size))
        
    data = CreateGroupPostData(match_results, args.type, args.groupname)
    new_group_id = jss.create_group(data)
    print("the new Static Group has been created at ID: {0}".format(new_group_id))
    sys.exit(0)