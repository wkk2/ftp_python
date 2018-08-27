import socketserver,os
import hashlib
import json
from core import users  # 同一个文件夹下
from conf.setting import *
import time

print(sys.path)

class MyTCPHandler(socketserver.BaseRequestHandler):
    def put(self,  msg_dict):
        error_code = {
            '300':'文件存在',
            }
        #self.request.send('200'.encode())
        filename = msg_dict['filename']
        filesize = msg_dict['filesize']
        current_dir = msg_dict['current_dir']
        current_user = current_dir.split('\\')[0]
        filepath = os.path.join(DATA_DIR,current_dir,filename)
        if os.path.isfile(filepath):
            self.request.send('300'.encode())
            while True:
                print('.....???')
                client_response = self.request.recv(1024).decode().lower()
                print(client_response)
                if client_response == 'y':
                    f = open(filepath,'wb')
                    break
                else:
                    print('in while!')
                    return
        else:
            self.request.send('OK'.encode())
            f = open(filepath,'wb')
        m = hashlib.md5()
        received_size = 0
        while received_size < filesize:
            if filesize - received_size < 1024:
                size = filesize - received_size
            else:
                size = 1024
            data = self.request.recv(size)
            f.write(data)
            m.update(data)
            received_size += len(data)
        f.close()
        user = users.User(current_user)
        old_disk_quota = user.user_read['disk_quota']
        new_disk_quota = (old_disk_quota*(2**30)-filesize)/(2**30)
        user.update_disk_quota(new_disk_quota)
        new_hash_code = m.hexdigest()
        old_has_code = self.request.recv(1024).decode()
        if new_hash_code == old_has_code:
            print('Upload success!!')
        else:
            print('file put broken!!')

    def get(self, msg_dict):
        filename = msg_dict['filename']
        current_dir = msg_dict['current_dir']
        filepath = os.path.join(DATA_DIR,current_dir,filename)
        if os.path.isfile(filepath):
            filesize = os.stat(filepath).st_size
            file_info = {
                'filesize':filesize,
            }
            m = hashlib.md5()
            self.request.send(json.dumps(file_info).encode())
            f = open(filepath, 'rb')
            for line in f:
                self.request.send(line)
                m.update(line)
            self.request.send(m.hexdigest().encode())
            print('Send file successful!')
        else:
            self.request.send('300'.encode())

    def auth(self):
        while True:
            user_info = json.loads(self.request.recv(1024).decode())
            username = user_info['username']
            password = user_info['password']
            user = users.User(username)
            print(user.user_file)
            print(user.user_read)
            print(user.get_user())
            if user.get_user():
                print(user.user_read)
                if user.user_read['password'] == password:
                    if user.user_read['status'] == '1':
                        self.request.send('500'.encode())
                        continue
                    #user.update_status_close()
                    self.request.send(json.dumps(user.user_read).encode())
                    print('[%s] login in ..' % username)
                    break
                    #return user
                else:
                    self.request.send('400'.encode())
                    print('Wrong password!')
            else:
                self.request.send('300'.encode())
                print('No this user!')
   #为什么只在第一次循环的时候进入？第一次循环进入之后游标处于末尾了
                              #下次再进入时继续读取后面的则没有东西可读了，必须要用seek函数把游标移到文件头


    def cd(self,msg_dict):
        server_response_code = {
            '300': 'dir is not exists!'
        }
        target_dir = msg_dict['dir']
        target_dir = os.path.join(DATA_DIR,target_dir)
        if os.path.exists(target_dir):
            self.request.send('OK'.encode())
        else:
            self.request.send('300'.encode())

    def mkdir(self,msg_dict):
        target_dir = msg_dict['target_dir']
        target_dir = os.path.join(DATA_DIR,target_dir)
        print(target_dir)
        if os.path.exists(target_dir):
            self.request.send('300'.encode())
        else:
            os.system('mkdir %s' % target_dir)
            self.request.send('OK'.encode())

    def dir(self,msg_dict):
        print('in dir')
        target_dir = msg_dict['current_dir']
        target_dir = os.path.join(DATA_DIR,target_dir)
        dir_info = os.popen('%s %s' % ('dir',target_dir)).read()
        print(type(dir_info))
        self.request.send(dir_info.encode())

    def handle(self):
        #conn, addr = server.accept()
        try:
            self.auth()
            while True:
                msg = self.request.recv(1024).decode()
                if msg == 'break':
                    print('Client break!')
                    break
                else:
                    msg_dict = json.loads(msg)
                    action = msg_dict['action']
                    print('action:',action)
                    if hasattr(self,'%s' % action):
                        func = getattr(self,'%s' % action)
                        print('func:',func)
                        func(msg_dict)
                    else:
                        print('wrong action!')
        except ConnectionResetError as e:
            print('Client break!')
#切换目录不要尝试用 os.system()、os.popen 等命令，每执行一次命令都相当于开启一个新的cmd命令窗口，
# 命令结束了之后该窗口也就关闭，相当于没有执行，
# 用os.chdir()也并不好使，这相当于切换了socketserver的工作目录
#解决方法：服务端实际上不切换目录，只在客户端上显示切换目录

if __name__ == '__main__':
    host,port = '127.0.0.1', 8899
    server = socketserver.ThreadingTCPServer((host,port), MyTCPHandler)
    server.serve_forever()

