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
invite_resp = "SIP/2.0 100 Trying\r\n\r\nSIP/2.0 180 Ringing\r\n\r\n"
invite_resp += "SIP/2.0 200 OK\r\n"
bad_request = "SIP/2.0 400 Bad Request\r\n"
not_allowed = "SIP/2.0 405 Method Not Allowed\r\n"
aEjecutar = "./mp32rtp -i ip -p port < audio"


class SIPHandler(socketserver.DatagramRequestHandler):
    mp32rtp = []

    def handle(self):
        message = self.rfile.read().decode('utf-8')
        ip = self.client_address[0]
        port = self.client_address[1]
        log.received_from(ip, port, message)
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
                    new_line = line.replace(user, config['account_username'])
                    new_line = new_line.replace(ip, config['uaserver_ip'])
                    sdp_body += new_line + '\r\n'
                elif 'm=' in line:
                    rtpaudio = line.split()[1]
                    self.mp32rtp.append(rtpaudio)
                    rtpport = config['rtpaudio_puerto']
                    sdp_body += line.replace(rtpaudio, rtpport) + '\r\n'
                else:
                    sdp_body += line + '\r\n'
            self.wfile.write(bytes(invite_resp + sdp_body, 'utf-8'))
            log.sent_to(ip, port, invite_resp + sdp_body)
        elif method == 'ACK':
            comando = aEjecutar.replace('ip', self.mp32rtp[0])
            comando = comando.replace('port', self.mp32rtp[1])
            comando = comando.replace('audio', config['audio_path'])
            print('enviando audio a', self.mp32rtp[0] + ':' + self.mp32rtp[1])
            os.system(comando)
        elif method == 'BYE':
            ok = 'SIP/2.0 200 OK\r\n'
            self.wfile.write(bytes(ok, 'utf-8'))
            log.sent_to(ip, port, ok)
        else:
            self.wfile.write(bytes(not_allowed, 'utf-8'))
            log.sent_to(ip, port, not_allowed)

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
    server_address = (config['uaserver_ip'], int(config['uaserver_puerto']))
    server = socketserver.UDPServer(server_address, SIPHandler)
    log = Log(config['log_path'])

    print('Listening...')
    try:
        log.starting()
        server.serve_forever()
    except KeyboardInterrupt:
        log.finishing()
        print("Finalizado servidor")
