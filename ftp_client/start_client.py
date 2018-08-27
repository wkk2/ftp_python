import sys,os

print(sys.path)
import ftp_client
client = ftp_client.FtpClient()
client.connect('127.0.0.1', 8899)
client.interactive()
