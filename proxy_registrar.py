# /usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import socket
import hashlib
import socketserver
from datetime import datetime, date, time, timedelta
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

usage_error = 'Usage: python proxy_registrar.py config'
TRYING = b"SIP/2.0 100 Trying\r\n"
RINGING = b"SIP/2.0 180 Ringing\r\n"
OK = b"SIP/2.0 200 OK\r\n"
BAD_REQUEST = b"SIP/2.0 400 Bad Request\r\n"
Not_Allowed = b"SIP/2.0 405 Method Not Allowed\r\n"
aEjecutar = "./mp32rtp -i 127.0.0.1 -p 23032 < "


def digest_nonce(server_name, ip):
    d = hashlib.sha512()
    d.update(bytes(server_name + ip, 'utf-8'))
    d.digest()
    return d.hexdigest()


def digest_response(nonce, username, passwd):
    d = hashlib.sha512()
    d.update(bytes(nonce + username + passwd, 'utf-8'))
    d.digest()
    return d.hexdigest()


class Log:

    def __init__(self, path):
        if not os.path.exists(path):
            os.system('touch ' + path)
        self.path = path

    def write(self, msg):
        with open(self.path, 'a') as logfile:
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            logfile.write(now, msg)

    def starting(self):
        msg = 'Starting...\n'
        self.write(msg)

    def sent_to(self, ip, port, mess):
        m = mess.replace('\r\n', ' ')
        msg = 'Sent to ' + ip + ':' + str(port) + ': ' + m + '\n'
        self.write(msg)

    def received_from(self, ip, port, mess):
        m = mess.replace('\r\n', ' ')
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
        self.dicc = {'server': {'name': '', 'ip': '', 'puerto': ''},
                     'database': {'path': '', 'passwdpath': ''},
                     'log': {'path': ''}}
        self.data = {}

    def startElement(self, name, attrs):
        if name in self.dicc:
            for att in self.dicc[name]:
                self.data[name + '_' + att] = attrs.get(att, '')

    def get_tags(self):
        return self.data


class SIPRegisterHandler(socketserver.DatagramRequestHandler):

    dicc = {}
    passwd = {}

    def handle(self):
        self.json2registered()
        self.json2passwd()
        message = self.rfile.read().decode('utf-8')
        method = message.split()[0]
        print(method, 'received')
        if method == 'REGISTER':
            user = message.split()[1].split(':')[1]
            if user in self.dicc:
                exp = message.split('\n')[1].split(':')[1]
                if int(expires) == 0:
                    del self.dicc[user]
                else:
                    exp_time = datetime.now() + timedelta(seconds=int(exp))
                    exp_date = exp_time.strftime('%H:%M:%S %d-%m-%Y')
                    self.dicc[user]['expires'] = exp_date
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            else:
                if 'Authorization' in message:
                    resp_user = message.split('\n')[2].split('"')[1]
                    server_name = config['server_name']
                    server_ip = config['server_ip']
                    nonce = digest_nonce(server_name, server_ip)
                    username = message.split('\n')[0].split(':')[1]
                    passwd = self.passwd[username]
                    response = digest_response(nonce, username, passwd)
                    if resp_user == response:
                        expires = message.split('\n')[1].split(':')[1]
                        ip = self.client_address[0]
                        port = message.split()[1].split(':')[2]
                        address = ip + ':' + port
                        now = datetime.now()
                        exp_time = now + timedelta(seconds=int(expires))
                        exp_date = exp_time.strftime('%H:%M:%S %d-%m-%Y')
                        self.dicc[user] = {'address': address,
                                           'expires': expires_time}
                        self.wfile.write(b'SIP/2.0 200 OK\r\n')
                    else:
                        self.wfile.write(b'SIP/2.0 400 Bad Request\r\n')
                else:
                    server_name = config['server_name']
                    server_ip = config['server_ip']
                    nonce = digest_nonce(server_name, server_ip)
                    mess = 'SIP/2.0 401 Unauthorized\nWWW Authenticate: ' + \
                           'Digest nonce="' + nonce + '"\r\n'
                    self.wfile.write(bytes(mess, 'utf-8'))
        elif method == 'INVITE':
            user_src = message.split('\r\n')[4].split()[0].split('=')[1]
            user_dst = message.split()[1].split(':')[1]
            if user_src in self.dicc and user_dst in self.dicc:
                mess = self.sent_to(user_dst, message)
                self.wfile.write(bytes(mess, 'utf-8'))
            else:
                self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
        elif method == 'ACK':
            print(message.split())
            user_dst = message.split()[1].split(':')[1]
            if user_dst in self.dicc:
                mess = self.sent_to(user_dst, message)
                self.wfile.write(bytes(mess, 'utf-8'))
        elif method == 'BYE':
            user_dst = message.split()[1].split(':')[1]
            if user_dst in self.dicc:
                mess = self.sent_to(user_dst, message)
                self.wfile.write(bytes(mess, 'utf-8'))
            else:
                self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
        else:
            self.wfile.write(Not_Allowed)
        self.registered2json()

    def sent_to(self, user, mess):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ip = self.dicc[user]['address'].split(':')[0]
            port = int(self.dicc[user]['address'].split(':')[1])
            my_socket.connect((ip, port))
            my_socket.send(bytes(mess, 'utf-8'))
            try:
                data = my_socket.recv(1024).decode('utf-8')
            except:
                data = ''
        return data

    def expires(self):
        now = datetime.now().strftime('%H:%M:%S %d-%m-%Y')
        del_list = []
        for usuario in self.dicc:
            if now >= self.dicc[usuario]['expires']:
                del_list.append(usuario)
        for user in del_list:
            del self.dicc[user]

    def registered2json(self):
        with open(config['database_path'], 'w') as jsonfile:
            json.dump(self.dicc, jsonfile, indent=3)

    def json2registered(self):
        self.expires()
        try:
            with open(config['database_path'], 'r') as jsonfile:
                self.dicc = json.load(jsonfile)
        except:
            pass

    def json2passwd(self):
        try:
            with open(config['database_passwdpath'], 'r') as jsonfile:
                self.passwd = json.load(jsonfile)
        except:
            pass

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
    server_address = (config['server_ip'], int(config['server_puerto']))
    server = socketserver.UDPServer(server_address, SIPRegisterHandler)

    print('Listening...')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
