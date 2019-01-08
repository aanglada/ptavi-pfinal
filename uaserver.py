# /usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import XMLHandler
from proxy_registrar import Log

usage_error = 'Usage: python uaserver.py config'
TRYING = b"SIP/2.0 100 Trying\r\n"
RINGING = b"SIP/2.0 180 Ringing\r\n"
OK = b"SIP/2.0 200 OK\r\n"
BAD_REQUEST = b"SIP/2.0 400 Bad Request\r\n"
Not_Allowed = b"SIP/2.0 405 Method Not Allowed\r\n"
aEjecutar = "./mp32rtp -i 127.0.0.1 -p 23032 < " 

class SIPHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        message = self.rfile.read().decode('utf-8')
        METHOD = self.line[0]
        if METHOD == 'INVITE':
            print('INVITE received')
            self.wfile.write(TRYING + b'\r\n' + RINGING + b'\r\n'
                             + OK + b'\r\n')
        elif METHOD == 'ACK':
            print("ACK RECIVED")
            os.system(aEjecutar)
        elif METHOD == 'BYE':
            print("BYE RECIVED")
            self.wfile.write(OK + b'\r\n')
        else:
            print("METHOD NOT ALLOWED")
            self.wfile.write(Not_Allowed + b'\r\n')

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
    server = socketserver.UDPServer((config['uaserver_ip'], int(config['uaserver_puerto'])), SIPHandler)
    
    print('Listening...')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
