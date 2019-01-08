# /usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import socket
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

usage_error = 'Usage: python proxy_registrar.py config'
TRYING = b"SIP/2.0 100 Trying\r\n"
RINGING = b"SIP/2.0 180 Ringing\r\n"
OK = b"SIP/2.0 200 OK\r\n"
BAD_REQUEST = b"SIP/2.0 400 Bad Request\r\n"
Not_Allowed = b"SIP/2.0 405 Method Not Allowed\r\n"
aEjecutar = "./mp32rtp -i 127.0.0.1 -p 23032 < " 

class Log:

    def __init__(self, path):
        if not os.path.exists(path):
            os.system('touch ' + path)
        self.path = path

    def write(self, msg):
        with open(self.path,'a') as logfile:
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            logfile.write(now,msg)

    def starting(self):
        msg = 'Starting...\n'
        self.write(msg)

    def sent_to(self, ip, port, mess):
        m = mess.replace('\r\n',' ')
        msg = 'Sent to ' + ip + ':' + str(port) + ': ' + m + '\n'
        self.write(msg)

    def received_from(self, ip, port, mess):
        m = mess.replace('\r\n',' ')
        msg = 'Received from ' + ip + ':' + str(port) + ': ' + m + '\n'
        self.write(msg)

    def error(self, error_mess):
        msg = 'Error: ' + error_mess + '\n'
        self.write(msg)

    def finishing(self):
        msg = 'Finishing...\n'
        self.write(msg)


class XMLHandler(ContentHandler):

    def __init__(self):
        self.dicc = {'server':{'name':'','ip':'','puerto':''},
                     'database':{'path':'','passswdpath':''},
                     'log':{'path':''}}
        self.data = {}

    def startElement(self, name, attrs):
        if name in self.dicc:
            for att in self.dicc[name]:
                self.data[name + '_' + att] = attrs.get(att,'')

    def get_tags(self):
        return self.data

class SIPRegisterHandler(socketserver.DatagramRequestHandler):

    dicc = {}
    passwd = {}

    def handle(self):
        message = self.rfile.read().decode('utf-8')
        method = message.split()[0]
        print(method)
        if method == 'REGISTER':
            # p4
            pass
        elif method == 'INVITE':
            print('INVITE received')
            self.wfile.write(TRYING + b'\r\n' + RINGING + b'\r\n' + OK + b'\r\n')
        elif method == 'ACK':
            print("ACK RECIVED")
            os.system(aEjecutar)
        elif method == 'BYE':
            print("BYE RECIVED")
            self.wfile.write(OK + b'\r\n')
        else:
            self.wfile.write(Not_Allowed)

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    if len(sys.argv) != 2:
        sys.exit(usage_error)
    else:
        xmlfile = sys.argv[1]
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(xmlfile))
    config = cHandler.get_tags()
    server = socketserver.UDPServer((config['server_ip'], int(config['server_puerto'])), SIPRegisterHandler)
    
    print('Listening...')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
