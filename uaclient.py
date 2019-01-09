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
aEjecutar = "./mp32rtp -i ip -p port < audio" 

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

    methods_allowed = ['register', 'invite', 'bye', 'ack']

    def __init__(self, xmlfile):
        parser = make_parser()
        cHandler = XMLHandler()
        parser.setContentHandler(cHandler)
        parser.parse(open(xmlfile))
        self.config = cHandler.get_tags()

    def register(self, option, digest=''):
        message = 'REGISTER sip:' + self.config['account_username'] + \
        ':' + self.config['uaserver_puerto'] + ' SIP/2.0\r\nExpires: ' + option
        if digest != '':
            message += '\r\nAuthorization: Digest response="' + digest + '"'
        
        return message + '\r\n'
        
    def invite(self, option):
        message = 'INVITE sip:' + option + ' SIP/2.0\r\n' + \
                  'Content-Type: application/sdp\r\n\r\nv=0\r\no=' + \
                  self.config['account_username'] + ' ' + \
                  self.config['uaserver_ip'] + '\r\ns=misesion\r\nt=0\r\n' + \
                  'm=audio ' + self.config['rtpaudio_puerto'] + ' RTP\r\n'
        return message

    def ack(self, option):
        message = 'ACK sip:' + option + ' SIP/2.0\r\n'
        return message

    def bye(self, option):
        message = 'BYE sip:' + option + ' SIP/2.0\r\n'
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
            m = method.upper() + ' sip:' + self.config['account_username'] + ' SIP/2.0\r\n'
            
        print("Enviando:\n" + m)
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

def trying_ringing_ok(data):
    trying ='100' in data
    ringing = '180' in data
    ok = '200' in data

    return trying and ringing and ok

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
        print('Recibido:\n' + data)
        if 'SIP/2.0 401 Unauthorized' in data:
            nonce = data.split('\r\n')[1].split('"')[1]
            user = client.config['account_username']
            passwd = client.config['account_passwd']
            response = digest_response(nonce, user, passwd)
            client.send(my_socket, method, option, response)
            data = client.receive(my_socket)
            print('Recibido:\n' + data)
        elif trying_ringing_ok(data):
            sdp = data.split('\r\n')[-7:-1]
            ip = sdp[1].split()[1]
            port = sdp[-2].split()[1]
            audio = client.config['audio_path']
            client.send(my_socket, 'ack', option)
            mp32rtp = aEjecutar.replace('ip', ip).replace('port', port).replace('audio', audio)
            print('enviando audio a', ip + ':' + port + '...')
            os.system(mp32rtp)
        else:
            pass
