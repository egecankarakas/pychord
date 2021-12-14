import socket
import hashlib
import socketio
from aiohttp import web








class node:
    def __init__(next, previous):
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        self.NodeId = hashlib.sha1(self.ip.encode()) 
        # we take the last 2 digits of ip as key
        self.NodeKey = self.ip.split('.')[-1]
        self.NodeKeyID = hashlib.sha1(self.NodeKey.encode())

    
    

    
    
        




