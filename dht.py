import socket
import threading
import os
import hashlib
import json
from pathlib import Path
import logging
import time


class Dht:

    def __init__(self):
        with open("./config.json") as json_data_file:
            self.config = json.load(json_data_file)
        logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=Path(self.config['logLocation']) / 'dht.log', filemode='w', level=logging.INFO)
        self.logger2 = logging.getLogger('DHT')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nodeList = []
        self.accept_connections()

    def accept_connections(self):
        ip = socket.gethostbyname(socket.gethostname())
        port = self.config["port"]
        self.s.bind((ip, port))
        self.s.listen(600)
        self.logger2.info('Running on IP: '+ip)
        self.logger2.info('Running on port: '+str(port))
        threading.Thread(target=self.ping_test_clients,
                         args=()).start()
        while 1:
            c, addr = self.s.accept()
            self.logger2.info('Client registered '+str(addr))
            threading.Thread(target=self.handle_client,
                             args=(c, addr,)).start()

    # ping test every 2 mins
    def ping_test_clients(self):
        # starttime = time.time()
        while True:
            for n in self.nodeList:
                try:
                    childS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    childS.connect((socket.gethostbyname(
                        socket.gethostname()), int(n['port'])))
                    childS.shutdown(2)
                    childS.close()
                except:
                    n['active'] = False
            time.sleep(120)
            self.logger2.info(self.nodeList)
            # time.sleep(120.0 - ((time.time() - starttime) % 60.0))

    def handle_client(self, c, addr):
        try:
            while True:
                data = c.recv(1024).decode()
                # if(data == 'deregisterNode'):
                #     c.send('port'.encode())
                #     port = int(c.recv(1024).decode())
                #     self.logger2.info('Deregistering the node '+str(port))
                #     for n in self.nodeList:
                #         if n['port'] == port:
                #             n['active'] = False
                #     continue
                if(data == 'registerNode'):
                    c.send('port'.encode())
                    port = int(c.recv(1024).decode())
                    self.logger2.info('Registering the node '+str(port))
                    c.send('file list'.encode())
                    files = eval(c.recv(1024).decode())
                    self.nodeList.append(
                        {'port': port, 'childPort': addr[1], 'files': files, 'active': True})
                    self.logger2.info(self.nodeList)
                    self.logger2.info('Registered the node '+str(port))
                    c.sendall('registered successfully'.encode())
                    continue
                if(data == 'updateNode'):
                    # c.send('port'.encode())
                    # port = int(c.recv(1024).decode())
                    c.send('file list'.encode())
                    files = eval(c.recv(1024).decode())
                    for n in self.nodeList:
                        if n['childPort'] == addr[1]:
                            n['files'] = files
                            self.logger2.info(
                                'updated the file list of the node '+str(n['port']))
                    self.logger2.info(self.nodeList)
                    c.sendall('updated successfully'.encode())
                    continue
                if(data == 'listoffiles'):
                    files = []
                    # c.send('port'.encode())
                    # port = int(c.recv(1024).decode())
                    for n in self.nodeList:
                        if n['active'] == True and n['childPort'] != addr[1]:
                            for l in n['files']:
                                files.append(
                                    {'port': n['port'], 'fileName': l})
                        else:
                            self.logger2.info(
                                'Sent list of files to '+str(n['port']))
                    files = str(files)
                    files = files.encode()
                    c.sendall(files)
                    continue
        except:
            for n in self.nodeList:
                if n['childPort'] == addr[1]:
                    n['active'] = False
                    self.logger2.info('Node deactivated '+str(n['port']))
                    break
            self.logger2.info(self.nodeList)


# dht = Dht()
