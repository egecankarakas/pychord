import argparse
import asyncio
import logging

import nest_asyncio

from node import EchoServerClientProtocol, Node

nest_asyncio.apply()


def main():
    global PYTHONASYNCIODEBUG
    PYTHONASYNCIODEBUG = 1
    logging.basicConfig(filename='chord.log', level=logging.DEBUG)
    for handler in logging.getLogger().handlers:
        if not isinstance(handler, logging.StreamHandler):
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(hostname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
    parser = argparse.ArgumentParser(description='Start Chord Node.')
    parser.add_argument('--ip', type=str, required=True,
                        help='IP address to run chord at')
    parser.add_argument('--bootstrap', type=str,
                        help='Bootstrap Server Chord Node IP address')
    args, _ = parser.parse_known_args()
    loop = asyncio.new_event_loop()
    if args.bootstrap:
        node = Node(ip=args.ip, bootstrap_server=args.bootstrap)
    else:
        node = Node(ip=args.ip)
    loop.run_until_complete(node.run(loop))

    #     print("Cancelling tasks")
    #     # node._server.close()
    #     # task.cancel()
    #     loop.close()


if __name__ == "__main__":
    main()
