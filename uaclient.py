#/usr/bin/python3
#-*-coding: utf-8-*-

import os
import sys
import socket
from datetime import datetime
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from proxy_registrar import Log, digest_response

usage_error = 'usage error: python3 uaclient.py config.xml method option'

class XMLHandler(ContentHandler):

    def __init__(self):
        self.dicc = {'account':{'username':'','passwd':''},
                     'uaserver':{'ip':'','puerto':''},
                     'rtpaudio':{'puerto':''},
                     'regproxy':{'ip':'','puerto':''},
                     'log':{'path':''},
                     'audio':{'path':''}}
        self.data = {}

    def startElement(self, name, attrs):
        if name in self.dicc:
            for att in self.dicc[name]:
                self.data[name + '_' + att] = attrs.get(att,'')

    def get_tags(self):
        return self.data


class ClientHandler:

    methods_allowed = ['register','invite','bye']

    def __init__(self, xmlfile):
        parser = make_parser()
        cHandler = XMLHandler()
        parser.setContentHandler(cHandler)
        parser.parse(open(xmlfile))
        self.config = cHandler.get_tags()

    def register(self, option):
        message = method.upper() + ' sip:' + self.config['account_username'] + \
        ':' + self.config['uaserver_puerto'] + 'SIP/2.0\nExpires: ' + option + \
        '\r\n'
        return message
        
    def invite(self, option):
        message = method.upper() + ' sip:' + option + ' SIP/2.0\n' + \
                  'Content-Type: application/sdp\n' + 'v=0\n' +'o=' + \
                  self.config['account_username'] + ' ' + \
                  self.config['uaserver_ip'] + 's=misesion\n' + 't=0\n' + \
                  'm=audio ' + self.config['uaserver_puerto'] + ' RTP\r\n'
        return message

    def ack(self, option):
        message = method.upper() + ' sip' + option + ' SIP/2.0\r\n'
        return message

    def bye(self, option):
        message = method.upper() + ' sip:' + option + ' SIP/2.0\r\n'
        return message


    def send(self, method, option):
    
        if method.lower() in self.methods_allowed:
            if method.lower() == 'register':
                m = self.register(option)
            elif method.lower() == 'invite':
                m = self.invite(option)
            elif method.lower() == 'bye':
                m = self.bye(option)
            elif method.lower() == 'ack':
                m = self.ack(option)
        else:
            mess = method.upper() + ' sip:' + self.config['account_username'] + ' SIP/2.0\r\n'
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            proxy = (self.config['regproxy_ip'],int(self.config['regproxy_puerto']))
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect(proxy)
            print("Enviando: " + m)
            my_socket.send(bytes(m, 'utf-8'))
            
    def get_mess(self, method, option):
            if str.lower(method) == 'register':
                return self.register(option)
            elif str.lower(method) == 'invite':
                return self.invite(option)
            elif str.lower(method) == 'bye':
                return self.bye(option)
            elif str.lower(method) == 'ack':
                return self.ack(option)

?
if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(usage_error)
    else:
        xmlfile = sys.argv[1]
        method = sys.argv[2]
        option = sys.argv[3]
    
    client = ClientHandler(xmlfile)
    client.send(method, option)
