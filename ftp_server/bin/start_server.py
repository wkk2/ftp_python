import os,sys
import socketserver

BASE_DIR = os.path.dirname(os.path.abspath('.'))
#print(BASE_DIR)
#print(sys.path)
sys.path.append(BASE_DIR)

from core import ftpServer
from conf.setting import *

server = socketserver.ThreadingTCPServer(IP_PORT, ftpServer.MyTCPHandler)
server.serve_forever()