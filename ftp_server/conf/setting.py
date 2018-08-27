import os,sys

BASE_DIR = os.path.abspath('.')
#print(BASE_DIR)
BASE_DIR = os.path.dirname(BASE_DIR)
#print(BASE_DIR)
#print(sys.path)
sys.path.append(BASE_DIR)
print(sys.path)
DATA_DIR = os.path.join(BASE_DIR,'data')
USER_FILE = os.path.join(DATA_DIR, 'userinfo')
IP_PORT = ('127.0.0.1', 8899)