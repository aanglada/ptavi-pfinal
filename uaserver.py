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
trying = "SIP/2.0 100 Trying\r\n\r\nSIP/2.0 180 Ringing\r\n\r\nSIP/2.0 200 OK\r\n"
bad_request = "SIP/2.0 400 Bad Request\r\n"
not_allowed = "SIP/2.0 405 Method Not Allowed\r\n"
aEjecutar = "./mp32rtp -i ip -p port < audio" 

class SIPHandler(socketserver.DatagramRequestHandler):
    mp32rtp = []

    def handle(self):
        message = self.rfile.read().decode('utf-8')
        method = message.split()[0]
        print(method, 'received')
        if method == 'INVITE':
            sdp = message.split('\r\n')[1:]
            sdp_body = ''
            for line in sdp:
                if 'o=' in line:
                    user = line.split('=')[1].split()[0]
                    ip = line.split('=')[1].split()[1]
                    self.mp32rtp.append(ip)
                    new_line = line.replace(user, config['account_username']).replace(ip, config['uaserver_ip'])
                    sdp_body += new_line + '\r\n'
                elif 'm=' in line:
                    rtpaudio = line.split()[1]
                    self.mp32rtp.append(rtpaudio)
                    sdp_body += line.replace(rtpaudio, config['rtpaudio_puerto']) + '\r\n'
                else:
                    sdp_body += line + '\r\n'
            response = trying + sdp_body
            print(response)
            self.wfile.write(bytes(response, 'utf-8'))
        elif method == 'ACK':
            comando = aEjecutar.replace('ip', self.mp32rtp[0]).replace('port', self.mp32rtp[1])
            comando = comando.replace('audio', config['audio_path'])
            os.system(comando)
        elif method == 'BYE':
            self.wfile.write(bytes(ok, 'utf-8'))
        else:
            self.wfile.write(bytes(not_allowed, 'utf-8'))

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
