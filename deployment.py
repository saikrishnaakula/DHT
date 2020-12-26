import os
from node import Node
from dht import Dht
import logging
import json
import sys
import os
import shutil
import threading
from pathlib import Path
with open("config.json") as json_data_file:
    config = json.load(json_data_file)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filemode='w', filename=Path(
                        config['logLocation']) / 'deployment.log')


threading.Thread(target=Dht, args=()).start()

i = int(sys.argv[1]) + 1
print("creating hosting folders for nodes")
for i in range(1, i + 1):
    try:
        shutil.rmtree(Path(config['hostedFolder']) / str(i))
    except:
        print("no folder")
    os.mkdir(Path(config['hostedFolder']) / str(i))
    filename = str(i)+'.pdf'
    shutil.copy(Path(config['hostedFolder']) / '4.pdf',
                    Path(config['hostedFolder']) / str(i) / filename)
# os.system("cd ./files/ py testBed.py "+str(i))
print("creation done")
os.system("cd ..")
print("file download test " + str(i-1) + " node start")
j = 1
while(i >= j):
    file = ''
    if(j-1 == 0):
        file = ''
    else:
        file = str(j-1)+'.pdf'
    print("node number "+str(j)+" downloading file "+file)
    threading.Thread(target=Node, args=(j, file,)).start()
    j = j+1
print("file download test " + str(i-1) + " node end")
