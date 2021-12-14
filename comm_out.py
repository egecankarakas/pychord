import socket


class commout: 

    def __init__(self, listenPort = 6547):
        self.listenPort = listenPort
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host = socket.gethostname()
        self.socket.connect(("10.141.0.31",self.listenPort))
        print(self.socket.recv(2000).decode())
        self.socket.close()
    

hold = commout()
    



    

    

    




     
