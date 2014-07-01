#!/usr/bin/python


import simplejson as json
import urllib2
import argparse
import ConfigParser
import sys


class  ZabbixAPIException(Exception):
    pass


class  ZabbixAPI(object):
    """
    Assign / un-assign a host to template using Zabbix API.
 
    Attributes: 
    url: zabbix host url
    user: username with zabbix api access
    password: password of above mentioned user
    """
    __auth = ''
    __id = 0

    def __init__(self, url, user, password):
        self.__url = url.rstrip('/') + '/zabbix/api_jsonrpc.php'
        self.__user = user
        self.__password = password
        #We may need this tuple in future.
        self._zabbix_api_object_list = ('Action', 'Alert', 'APIInfo',
        'Application', 'DCheck', 'DHost', 'DRule', 'DService', 'Event',
        'Graph', 'Grahpitem', 'History', 'Host', 'Hostgroup', 'Image',
        'Item', 'Maintenance', 'Map', 'Mediatype', 'Proxy', 'Screen',
        'Script', 'Template', 'Trigger', 'User', 'Usergroup', 'Usermacro',
        'Usermedia')

    def login(self):
        user_info = {'user': self.__user,
                     'password': self.__password}
        obj = self.json_obj('user.login', user_info)
        content = self.postRequest(obj)
        try:
            self.__auth = content['result']
            #print self.__auth
            return self.__auth
        except KeyError, e:
            e = content['error']['data']
            raise ZabbixAPIException(e)

    def hostExist(self, host_name):
        host_ex_json = self.json_obj('host.exists', {'host': host_name})
        host_ex_data = self.postRequest(host_ex_json)
        host_exists = host_ex_data['result']
        if host_exists:
            host = {'host': host_name}
            host_id_json = self.json_obj('host.get', {'output': "extend",
                                                      'filter': host})
            #print "Json data sent for getting host id: " + host_id_json
            host_id_data = self.postRequest(host_id_json)
            host_id = host_id_data['result'][0]['hostid']
            return host_id

    def templateExist(self, temp_name):
        temp_ex_json = self.json_obj('template.exists', {'host': temp_name})
        temp_ex_data = self.postRequest(temp_ex_json)
        temp_exists = temp_ex_data['result']
        if temp_exists:
            temp = {'host': temp_name}
            temp_id_json = self.json_obj('template.get', {'output': "extend",
                                                        'filter': temp})
            temp_id_data = self.postRequest(temp_id_json)
            temp_id = temp_id_data['result'][0]['templateid']
            return temp_id

    def linkHost(self, host_id, temp_ids):
        temp_list = []
        for i in temp_ids:
            empty_dict = {}
            empty_dict['templateid'] = i
            temp_list.append(empty_dict)
        temp_ln_json = self.json_obj('host.update', {'hostid': host_id,
                                     'templates': temp_list})
        ln_update = self.postRequest(temp_ln_json)
        try:
            return ln_update['result']['hostids']
        except:
            print "ERROR: " + ln_update['error']['data']
            exit()

    def unlinkHost(self, host_id, temp_id):
        tem_data = {'templateid': temp_id}
        tem_un_json = self.json_obj('host.update', {'hostid': host_id,
                                    'templates_clear': tem_data})
        un_update = self.postRequest(tem_un_json)
        print un_update
        return un_update['result']['hostids']

    def listHosts(self, tempid):
        ls_data = {'templateid': tempid}
        ls_data_json = self.json_obj('host.get', {'templateids': ls_data})
        ls_hosts = self.postRequest(ls_data_json)
        j = []
        for i in ls_hosts['result']:
            k = self.getHost(i['hostid'])
            j.append(k)
        return j

    def listtempids(self, hostid):
        hs_data = {'host': hostid}
        hs_data_json = self.json_obj('template.get', {'output': "extend",
                                                      'hostids': hs_data})
        ls_tempids = self.postRequest(hs_data_json)
        o = []
        for i in ls_tempids['result']:
            o.append(i['templateid'])
        return o

    def getHost(self, host_id):
        hs_data = {'host': host_id}
        hs_data_json = self.json_obj('host.get', {'output': "extend",
                                                  'hostids': hs_data})
        hs_hostname = self.postRequest(hs_data_json)
        return hs_hostname['result'][0]['host']

    def listTemplates(self, hostid):
        ht_data = {'host': hostid}
        ht_data_json = self.json_obj('template.get', {'output': "extend",
                                                      'hostids': ht_data})
        temps = self.postRequest(ht_data_json)
        n = []
        for m in temps['result']:
            n.append(m['host'])
        return n

    def json_obj(self, method, params):
        obj = {'jsonrpc': '2.0',
                'method': method,
                'params': params,
                'auth': self.__auth,
                'id': self.__id}
        return json.dumps(obj)

    def postRequest(self, json_obj):
        #print 'Post: %s' % json_obj
        headers = {'Content-Type': 'application/json-rpc',
                   'User-Agent': 'python/zabbix_api'}
        req = urllib2.Request(self.__url, json_obj, headers)
        opener = urllib2.urlopen(req)
        content = json.loads(opener.read())
        self.__id += 1
        #print 'Receive: %s' % content
        return content


def ConfigSectionMap(section):
        dict1 = {}
        options = Config.options(section)
        for option in options:
            try:
                dict1[option] = Config.get(section, option)
                if dict1[option] == -1:
                    print "skip: %s" % option
            except:
                print "exception on %s!" % option
                dict1[option] = None
        return dict1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A script\
    that can assign or unassign a template to given host")
    parser.add_argument('--verbose', help='verbose mode', dest='v')
    subparsers = parser.add_subparsers()
    parser_assign = subparsers.add_parser('assign',
                    help='Assigns a template to given host')
    parser_assign.add_argument('-t', help='Template name', required=True)
    parser_assign.add_argument('-s', help='Server name', required=True)
    parser_assign.add_argument('-e', help='Environment',
                               dest='env', required=True)
    parser_unassign = subparsers.add_parser('unassign',
                      help='Unassigns a template to given host')
    parser_unassign.add_argument('-t', help='Template name', required=True)
    parser_unassign.add_argument('-s', help='Server name', required=True)
    parser_unassign.add_argument('-e', help='Environment',
                                  dest='env', required=True)
    parser_list = subparsers.add_parser('list',
                                         help='Lists the assigned templates')
    parser_list.add_argument('-s', help='Server name', required=True)
    parser_list.add_argument('-e', help='Environment',
                             dest='env', required=True)
    args = parser.parse_args()
    Config = ConfigParser.ConfigParser()
    #File containing the login info.
    Config.read("config_data")
    env = args.env
    #Zabbix url, username, password from config_data file
    url = ConfigSectionMap(env)['url']
    user = ConfigSectionMap(env)['username']
    password = ConfigSectionMap(env)['password']
    zapi = ZabbixAPI(url, user, password)
    auth = zapi.login()
    if sys.argv[1] == "list":
        #Code for listing the host goes here
        host = zapi.hostExist(args.s)
        if host:
            print "Trying to list the assigned templates,\
 This may take a while..."
            v = zapi.listTemplates(host)
            for m in v:
                print m
        else:
            print "Host not found!"
    else:
        if sys.argv[1] == "assign":
            host = zapi.hostExist(args.s)
            temp = zapi.templateExist(args.t)
            if host and temp:
                print """Trying to Link..."""
                ln_temp = zapi.listtempids(host)
                ln_temp.append(host)
                y = zapi.linkHost(host, ln_temp)
                if y:
                    print "Host: " + host + "has\
been linked to Template: " + temp
                else:
                    print "Template/Host not found, Please check!"

        else:
            host = zapi.hostExist(args.s)
            temp = zapi.templateExist(args.t)
            if host and temp:
                print """Trying to Unassign..."""
                z = zapi.unlinkHost(host, temp)
                print "Host: " + host + "has been unlinked from\
Template: " + temp
            else:
                print "Template/Host not found, Please check!"
