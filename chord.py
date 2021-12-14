from comm_out import commout  
from comm_in import commin
from node import node
import threading


def main_task():
    global mynode 
    mynode = node()

    lock = threading.Lock()

    server = threading.Thread(target=commin(), args=(lock,))
    
    server.start()


if __name__ == "__main__":
    main_task()


