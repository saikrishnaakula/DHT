import socket
import threading
import os
import hashlib
import json
from pathlib import Path
import logging
import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class Handler(PatternMatchingEventHandler):
    
    def __init__(self,childS,dataFolder): 
        self.dataFolder = dataFolder
        self.s = childS
        PatternMatchingEventHandler.__init__(self, patterns=['*.*'], 
                                                             ignore_directories=True, case_sensitive=False)

    def on_any_event(self,event):
        if event.is_directory:
            return None
        else:
            self.s.sendall('updateNode'.encode())
            if self.s.recv(1024).decode()=='file list':
                files = os.listdir(self.dataFolder)
                files = str(files)
                files = files.encode()
                self.s.sendall(files)
            logging.info(self.s.recv(1024).decode())
            logging.info("file updated %s." % event.src_path)


class Node:
    def __init__(self,nodeNum,fileName):
        with open("config.json") as json_data_file:
            self.config = json.load(json_data_file)
        self.dataFolder = Path(self.config['hostedFolder']) /str(nodeNum) 
        logName = 'node-'+str(nodeNum) +'.log'
        logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',filename=Path(
            self.config['logLocation']) / logName, filemode='w', level=logging.INFO)
        self.logger1 = logging.getLogger('node-'+str(nodeNum))
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_name = fileName
        self.accept_connections()

    def connect_to_dht(self):
        self.observer = Observer()
        self.target_ip = socket.gethostbyname(socket.gethostname())
        self.target_port = self.config["port"]
        childS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        childS.connect((self.target_ip, int(self.target_port)))
        childS.sendall('registerNode'.encode())
        if childS.recv(1024).decode() =='port':
            childS.sendall(str(self.port).encode())
        if childS.recv(1024).decode() =='file list':
            files = os.listdir(self.dataFolder)
            files = str(files)
            files = files.encode()
            childS.sendall(files)
        self.logger1.info('Node registered with DHT Server '+str(self.target_port))
        self.logger1.info(childS.recv(1024).decode())
        event_handler = Handler(childS,self.dataFolder)
        self.observer.schedule(event_handler, self.dataFolder, recursive=True)
        self.observer.start()
        if self.file_name == 0 :
            flag = input("download (y/n) -->")
        else:
            flag = 'y'
        if flag=='y':
            childS.sendall('listoffiles'.encode())
            data = childS.recv(4098).decode()
            for d in eval(data):
                print(d)       
            if self.file_name == 0:    
                self.file_name = input("enter file name to download -->")
            for d in eval(data):
                if d['fileName'] == self.file_name:
                    self.downloadFileSingle(d['port'],d['fileName'])
                    break

    def accept_connections(self):
        ip = socket.gethostbyname(socket.gethostname())
        self.s.bind((ip, 0))
        self.s.listen(50)
        self.port = self.s.getsockname()[1]
        self.logger1.info('Running on IP: '+ip)
        self.logger1.info('Running on port: '+str(self.port))
        threading.Thread(target=self.connect_to_dht, args=()).start()
        while 1:
            c, addr = self.s.accept()
            self.logger1.info('Client registered '+str(addr))
            threading.Thread(target=self.handle_client,
                             args=(c, addr,)).start()
        
    def md5(self, name):
        hash_md5 = hashlib.md5()
        with open(name, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def downloadFileSingle(self, port,file_name):
        DownloadS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        DownloadS.connect((self.target_ip, int(port)))
        DownloadS.sendall('md5'.encode())
        if DownloadS.recv(1024).decode() == 'fileName':
            DownloadS.sendall(file_name.encode())
        hash = DownloadS.recv(1024).decode()
        DownloadS.sendall('downloadfile'.encode())
        if DownloadS.recv(1024).decode() == 'fileName':
            DownloadS.sendall(file_name.encode())
        size = DownloadS.recv(1024).decode()
        if size == "file-doesn't-exist":
            print("File doesn't exist on server.")
            DownloadS.shutdown(socket.SHUT_RDWR)
            DownloadS.close()
        else:
            total = 0
            size = int(size)
            name = self.dataFolder / file_name
            with open(name, 'wb') as file:
                while 1:
                    data = DownloadS.recv(1024)
                    total = total + len(data)
                    file.write(data)
                    if total >= size:
                        break
                file.close()
            if hash == self.md5(name):
                print(file_name, 'successfully downloaded.')
            else:
                print(file_name, 'unsuccessfully downloaded.')
        DownloadS.shutdown(socket.SHUT_RDWR)
        DownloadS.close()
    
    def handle_client(self, c, addr):
        try:
            while True:
                data = c.recv(1024).decode()
                if(data == 'md5'):
                    c.sendall("fileName".encode())
                    c.sendall(self.md5(self.dataFolder /
                                    c.recv(1024).decode()).encode())
                    self.logger1.info('md5 token sent to '+str(addr))
                
                if(data == 'downloadfile'):
                    c.sendall("fileName".encode())
                    data = c.recv(1024).decode()
                    filePath = self.dataFolder / data
                    fileSize = str(os.path.getsize(filePath))
                    self.logger1.info('download requested for file ' +
                                data + ' size ' + fileSize
                                    + 'Bytes by '+str(addr))
                    if not os.path.exists(filePath):
                        self.logger1.info('file doesnt exit '+data + ' to '+str(addr))
                        c.sendall("file-doesn't-exist".encode())
                    else:
                        c.sendall(fileSize.encode())
                        self.logger1.info('sending file '+data + ' to '+str(addr))
                        if data != '':
                            tic = time.perf_counter()
                            file = open(filePath, 'rb')
                            fdata = file.read(1024)
                            while fdata:
                                c.sendall(fdata)
                                fdata = file.read(1024)
                            file.close()
                            toc = time.perf_counter()
                            totalTime = str(f"{toc - tic:0.4f} seconds")
                            self.logger1.info('file '+data + ' sent in ' + totalTime +' to '+str(addr))
                            self.logger1.info(totalTime)
                            c.shutdown(socket.SHUT_RDWR)
                            c.close()
        except:
            self.logger1.info('connection closed for '+str(addr[1]))
        
# node = Node(0,0)


