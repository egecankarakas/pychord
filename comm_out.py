import socket


class commout: 

    def __init__(self, listenPort = 6545):
        self.listenPort = listenPort
        #socket.AF_INET,socket.SOCK_STREAM
        self.socket = socket.socket()
        self.host = socket.gethostname()
        self.socket.connect(("10.141.0.66",self.listenPort))
        #print(self.socket.recv(2000).decode())
        #self.socket.close()
    
    def try_connect(self):
        
        self.socket.send("test".encode())
        response = self.socket.recv(1024)
        print(response.decode("utf-8"))
        #self.socket.close()
        

hold = commout()
hold.try_connect()
    



    

    

    




     
