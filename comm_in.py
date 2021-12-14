import socket


class commin: 

    def __init__(self, listenPort = 6547):
        self.listenPort = listenPort
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.hostname = socket.gethostname()
        self.ip = socket.gethostbyname(self.hostname)
        print(self.ip)
        self.socket.bind((self.ip, self.listenPort))
        self.socket.listen(5)

        while True:
            c, addr = self.socket.accept()
            print("Got commention form{}".format(addr))
            c.send('thanks'.encode())
            c.close()


hold = commin()
    


