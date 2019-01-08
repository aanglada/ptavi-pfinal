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

    def register(self, option, digest=''):
        message = method.upper() + ' sip:' + self.config['account_username'] + \
        ':' + self.config['uaserver_puerto'] + ' SIP/2.0\nExpires: ' + option
        if digest != '':
            message += '\nAuthorization: Digest response="'+ digest +'"'
        
        return message + '\r\n'
        
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


    def send(self, socket, method, option, digest=''):
    
        if method.lower() in self.methods_allowed:
            if method.lower() == 'register':
                m = self.register(option, digest)
            elif method.lower() == 'invite':
                m = self.invite(option)
            elif method.lower() == 'bye':
                m = self.bye(option)
            elif method.lower() == 'ack':
                m = self.ack(option)
        else:
            mess = method.upper() + ' sip:' + self.config['account_username'] + ' SIP/2.0\r\n'
        print("Enviando: " + m)
        socket.send(bytes(m, 'utf-8'))

    def receive(self, socket):
        try:
            data = socket.recv(1024).decode('utf-8')
        except:
            data = ''
            
        return data
            
    def get_mess(self, method, option, digest=''):
            if method.lower() == 'register':
                return self.register(option, digest)
            elif method.lower() == 'invite':
                return self.invite(option)
            elif method.lower() == 'bye':
                return self.bye(option)
            elif method.lower() == 'ack':
                return self.ack(option)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(usage_error)
    else:
        xmlfile = sys.argv[1]
        method = sys.argv[2]
        option = sys.argv[3]
    
    client = ClientHandler(xmlfile)
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy = (client.config['regproxy_ip'],int(client.config['regproxy_puerto']))
        my_socket.connect(proxy)
        client.send(my_socket, method, option)
        data = client.receive(my_socket)
        print(data)
        trying_ringing_ok = ('100' in data) and ('180') and ('200')
        if '401' in data:
            nonce = data.split('\n')[1].split('"')[1]
            user = client.config['account_username']
            passwd = client.config['account_passwd']
            response = digest_response(nonce, user, passwd)
            client.send(my_socket, method, option, response)
            data = client.receive(my_socket)
            print(data)
        elif trying_ringing_ok:
           pass
        else:
            pass
