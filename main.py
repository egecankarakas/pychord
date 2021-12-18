import asyncio
import argparse
import settings
import logging
from node import Node, EchoServerClientProtocol
import nest_asyncio
nest_asyncio.apply()


def main():
    global PYTHONASYNCIODEBUG
    PYTHONASYNCIODEBUG=1
    logging.basicConfig(filename='chord.log', level=logging.DEBUG)
    for handler in logging.getLogger().handlers:
        if not isinstance(handler,logging.StreamHandler):
            handler.setFormatter(logging.Formatter('%(asctime)s %(hostname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
    parser = argparse.ArgumentParser(description='Start Chord Node.')
    parser.add_argument('--ip', type=str, required=True,
                        help='IP address to run chord at')
    parser.add_argument('--bootstrap', type=str,
                        help='Bootstrap Server Chord Node IP address')
    args, _ = parser.parse_known_args()
    loop = asyncio.new_event_loop()
    if args.bootstrap:
        node=Node(ip=args.ip,bootstrap_server=args.bootstrap)
    else:
        node=Node(ip=args.ip)
    loop.run_until_complete(node.run(loop))
    # print("Creating Server task")
    # coro = loop.create_server(EchoServerClientProtocol, node.ip, settings.CHORD_PORT)
    # task=loop.create_task(node.update_periodically())
    # server=loop.run_until_complete(coro)
    

    # try:
    #     loop.run_forever()
    #     # while True:
    #     #     loop.run_until_complete(task)
    #     #     loop.run_until_complete(server)
    # except:
    #     print("Closing the server")
    #     loop.run_until_complete(server.wait_closed())
    # finally:
    #     print("Cancelling tasks")
    #     # node._server.close()
    #     # task.cancel()
    #     loop.close()

async def execute(self, loop,node):
    await loop.run_in_executor(None, node.update_periodically, None) 

if __name__ == "__main__":
    main()