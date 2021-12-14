import socket
from _thread import *


class commin: 

    def __init__(self, listenPort = 6545):
        self.listenPort = listenPort
        #socket.AF_INET,socket.SOCK_STREAM
        self.socket = socket.socket()
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        self.threadCount = 0 
        print(self.ip)
        self.socket.bind((self.ip, self.listenPort))
        
    
    def listenforConnections(self):
        self.socket.listen(5)
        while True:
            Client, address = self.socket.accept()
            print('Connected to: ' + address[0] + ':' + str(address[1]))
            start_new_thread(threaded_client, (Client, ))
            self.threadCount +=1
            print('Thread Number:{}'.format(self.threadCount))
        self.socket.close()




def threaded_client(connection):
    #connection.send(str.encode('Welcome to the Servern'))
    while True:
        data = connection.recv(2048)
        reply = 'Server Says: ' + data.decode('utf-8')
        if not data:
            break
        connection.sendall(str.encode(reply))
    connection.close()

    

hold = commin()
hold.listenforConnections()
