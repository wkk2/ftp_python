import socket
import os,json
import hashlib

class FtpClient(object):
    def __init__(self):
        self.client = socket.socket()
        self.user_current_dir = ''
        self.user_infos = {}
    def connect(self,ip,port):
        self.client.connect((ip,port))
    def interactive(self):
        self.auth()
        while True:
            cmd = input('%s>>' % self.user_current_dir).strip()
            if len(cmd) == 0:
                continue
            if cmd == 'q' or cmd == 'quit':
                self.client.send('break'.encode())
                break
            cmd_split = cmd.split()
            action = cmd_split[0]
            if hasattr(self,'cmd_%s' % action):
                func = getattr(self, 'cmd_%s' % action)
                func(cmd_split)
            else:
                print('Wrong cmd!')
                self.help()

    def cmd_dir(self,cmd_split):
        print('in client dir!')
        msg_dict = {
            'action': 'dir',
            'current_dir': self.user_current_dir,
        }
        self.client.send(json.dumps(msg_dict).encode())
        server_response = self.client.recv(1024).decode()
        print(server_response)

    def cmd_cd(self,cmd_split):
        if len(cmd_split) <= 1:
            print('Wrong cmd!')
        else:
            target_dir = cmd_split[1]
            if target_dir == '..':
                path_split = list(os.path.split(self.user_current_dir))
                if '' in path_split:
                    print('You are in the top dir!')
                    target_dir = self.user_current_dir
                else:
                    target_dir = path_split[0]
            elif target_dir == '.':
                target_dir = self.user_current_dir
            else:
                target_dir = os.path.join(self.user_current_dir, target_dir)
            msg_dict = {
                'action': 'cd',
                'dir': target_dir,
            }
            self.client.send(json.dumps(msg_dict).encode())
            server_response = self.client.recv(1024).decode()
            if server_response == 'OK':
                self.user_current_dir = target_dir
            else:
                print('[%s] is not exist!' % target_dir)

    def cmd_mkdir(self,cmd_split):
        if len(cmd_split) <= 1:
            print('wrong cmd!')
        else:
            dirname = cmd_split[1]
            target_dir = os.path.join(self.user_current_dir,dirname)
            msg_dict = {
                'action':'mkdir',
                'target_dir':target_dir
            }
            self.client.send(json.dumps(msg_dict).encode())
            server_response = self.client.recv(1024).decode()
            if server_response == 'OK':
                print('make dir [%s] success!' % dirname)
            else:
                print('The dir has already exists!')

    def cmd_put(self,cmd_split):
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            if os.path.isfile(filename):
                filesize = os.stat(filename).st_size
                print('filesize:', filesize)
                print('disk_quota:', self.user_infos["disk_quota"] * (2 ** 30))
                if filesize > self.user_infos["disk_quota"]*(2**30):
                    print('filesize:',filesize)
                    print('disk_quota:',self.user_infos["disk_quota"]*(2**30))
                    print('Space is not enough in the server!')
                else:
                    msg_dict = {
                        'action': 'put',
                        'filename': filename,
                        'filesize': filesize,
                        'current_dir': self.user_current_dir
                    }
                    self.client.send(json.dumps(msg_dict).encode())
                    server_response = self.client.recv(1024).decode()
                    #print(server_response)
                    flag = False
                    print(server_response)
                    if server_response == '300':
                        print('The file is exists in server, do you want to override it? (y/n)')
                        while True:
                            cmd = input().strip()
                            if cmd.lower() == 'y':
                                self.client.send('y'.encode())
                                flag = True
                                break
                            elif cmd.lower() == 'n':
                                self.client.send('n'.encode())
                                break
                            else:
                                print('wrong cmd!')
                    elif server_response == 'OK':
                        flag = True
                    if flag:
                        print('Start Uploading...')
                        send_size = 0
                        f = open(filename, 'rb')
                        m = hashlib.md5()
                        for line in f:
                            self.client.send(line)
                            send_size += len(line)
                            print('send %s'% (send_size/filesize))
                            m.update(line)
                        self.client.send(m.hexdigest().encode())
                        print('%s uploading success!' % filename)
                        self.user_infos['disk_quota'] = (self.user_infos["disk_quota"] * (2 ** 30)-filesize)/(2**30)
            else:
                print('%s is not exists!' % filename)
                return
        else:
            print('Wrong cmd !')

    def cmd_get(self,cmd_split):
        server_response_code = {
            '300': 'file is not exists in server',
        }
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            msg_dict = {
                'action': 'get',
                'filename': filename,
                'current_dir':self.user_current_dir
            }
            self.client.send(json.dumps(msg_dict).encode())
            server_response = self.client.recv(1024).decode()
            if server_response not in server_response_code:
                server_response = json.loads(server_response)
                print('Start downloading....')
                m = hashlib.md5()
                #filename = server_response['filename']
                filesize = server_response['filesize']
                f = open(filename, 'wb')
                recevied_size = 0
                while recevied_size < filesize:
                    if filesize - recevied_size < 1024:
                        size = filesize - recevied_size
                    else:
                        size = 1024
                    data = self.client.recv(size)
                    m.update(data)
                    f.write(data)
                    recevied_size += len(data)
                new_hash_code = m.hexdigest()
                old_hash_code = self.client.recv(1024).decode()
                if new_hash_code == old_hash_code:
                    print('Download success...')
            else:
                print(server_response_code[server_response])

    def help(self):
        msg = '''
        cd 
        mkdir
        put
        get
        dir
        '''
        print(msg)

    def auth(self):
        while True:
            username = input('username:')
            password = input('password:')
            user_info = {
                'username': username,
                'password': password,
            }
            self.client.send(json.dumps(user_info).encode())
            server_response = self.client.recv(1024).decode()
            if server_response == '300':
                print('No user !')
            elif server_response == '400':
                print('Wrong password!')
            elif server_response == '500':
                print('This account has been login in !')
            else:
                user = json.loads(server_response)
                self.user_current_dir = username
                self.user_infos = user
                print('user auth pass!')
                break

                #user = users.User(name)
                #user_info = user.get_user()
                #break

if __name__ == '__main__':
    client = FtpClient()
    client.connect('127.0.0.1', 8899)
    client.interactive()