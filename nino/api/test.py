import sys
sys.path.insert(0, "..")
sys.path.insert(0, "../pipeline")

import pipeline.main as m

request = "REQ"

import socket
host = socket.gethostname()  # get local machine name
port = 8080  # Make sure it's within the > 1024 $$ <65535 range

s = socket.socket()
s.connect((host, port))

s.send(request.encode('utf-8'))
s.close()

import os
os.mkdir("foo")
