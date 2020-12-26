import os 
import shutil
import sys

for i in range(1,int(sys.argv[1]) +1 ):
    try:
        # shutil.rmtree(str(i))
        os.mkdir(str(i))
        os.system('copy 4.pdf '+ str(i)+'\\'+str(i)+'.pdf')
    except:
        print("no folder")